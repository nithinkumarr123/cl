"""UCSC genomic windows and transcript-oriented coding sequences."""
from services.ucsc_service import ucsc_service
from utils.translation_utils import translate_cds
from data.transcript_metadata import TRANSCRIPT_METADATA
from loguru import logger

DNA_WINDOW = 5940  # Leave room for special tokens and short indels.


def replace_allele(sequence, index, ref, alt):
    if index < 0 or index + len(ref) > len(sequence):
        raise ValueError("Variant is outside the sequence")
    if sequence[index:index + len(ref)] != ref:
        logger.warning('REF mismatch at local index {}: supplied={} actual={}',
                       index, ref, sequence[index:index + len(ref)])
        raise ValueError("Reference allele does not match the reference sequence")
    return sequence[:index] + alt + sequence[index + len(ref):]


async def genomic_pair(variant):
    ref, alt = variant.reference_allele, variant.alternate_allele
    # Empty REF is ambiguous; insertions must include a genomic anchor base.
    if not ref or ref == alt:
        raise ValueError("Use a nonempty reference allele and a different alternate allele")
    if max(len(ref), len(alt)) > 1000:
        raise ValueError("Alleles longer than 1000 bases are unsupported")
    size = DNA_WINDOW - max(0, len(alt) - len(ref))
    locus = variant.position - 1
    start = max(0, locus - (size - len(ref)) // 2)
    end = start + size
    meta = TRANSCRIPT_METADATA.get(getattr(variant, "gene", ""), {})
    exon = next((exon for exon in meta.get("exons", [])
                 if exon["start"] <= variant.position <= exon["end"]), None)
    if exon:
        logger.info('Selected exon: {}:{}-{} (1-based inclusive), length={} bp',
                    variant.chromosome, exon['start'], exon['end'], exon['end'] - exon['start'] + 1)
        # Metadata is 1-based inclusive; UCSC expects 0-based half-open.
        exon_start, exon_end = exon["start"] - 1, exon["end"]
        if locus + len(ref) > exon_end:
            raise ValueError("Reference allele crosses the exon boundary")
        if exon_end - exon_start <= size:
            start, end = exon_start, exon_end
        else:
            start = min(max(exon_start, start), exon_end - size)
            end = start + size
            logger.info('Oversized exon: clipping to {} bp window', size)
    else:
        logger.info('No containing exon; using genomic window fallback')
    logger.info('DNA input fetch: {}:{}-{} (0-based half-open), expected={} bp',
                variant.chromosome, start, end, end - start)
    sequence = await ucsc_service.fetch_region(variant.chromosome, start, end, "hg38")
    if not sequence:
        raise RuntimeError("UCSC DNA retrieval failed")
    if len(sequence) != end - start:
        raise RuntimeError("UCSC returned a sequence outside the requested window")
    index = locus - start
    altered = replace_allele(sequence, index, ref, alt)
    logger.info('DNA REF verified; applied {}>{} at local index {} (0-based); ref={} bp alt={} bp',
                ref, alt or '<deletion>', index, len(sequence), len(altered))
    return sequence, altered, index, start


async def coding_reference(gene):
    """Join complete coding exon portions; never trim exon phase bases."""
    meta = TRANSCRIPT_METADATA[gene]
    lo, hi = sorted((meta["cds_start"], meta["cds_end"]))
    fragments, positions = [], []
    logger.info('Building {} reference CDS: transcript={} strand={}', gene, meta['refseq_mrna'], meta['strand'])
    for exon_index, exon in enumerate(sorted(meta["exons"], key=lambda e: e["start"]), 1):
        start, end = max(lo, exon["start"]), min(hi, exon["end"])
        if start > end:
            logger.debug('CDS exon {} skipped: no coding portion', exon_index)
            continue
        logger.info('CDS coding exon {}: chr{}:{}-{} (0-based half-open), {} bp',
                    exon_index, meta['chromosome'], start - 1, end, end - start + 1)
        fragment = await ucsc_service.fetch_region(meta["chromosome"], start - 1, end, "hg38")
        if not fragment or len(fragment) != end - start + 1:
            raise RuntimeError("UCSC coding exon retrieval failed")
        fragments.append(fragment)
        positions.extend(range(start, end + 1))
    cds = "".join(fragments)
    if meta["strand"] == -1:
        cds = ucsc_service.reverse_complement(cds)
        positions.reverse()
        logger.info('Joined {} coding fragments; reverse-complemented minus-strand CDS', len(fragments))
    protein = translate_cds(cds)
    if (len(cds) != meta["cds_length_bp"] or len(protein) != meta["protein_length_aa"]
            or not cds.startswith("ATG") or cds[-3:] not in ("TAA", "TAG", "TGA")):
        raise RuntimeError("UCSC CDS failed transcript length/translation validation")
    logger.info('{} reference CDS validated and translated: {} bp -> {} aa; start={} stop={}',
                gene, len(cds), len(protein), cds[:3], cds[-3:])
    return {"cds": cds, "protein": protein, "positions": positions,
            "transcript_id": meta["refseq_mrna"], "source": "ucsc_hg38_coding_exons"}


def coding_pair(reference, variant):
    positions = reference["positions"]
    affected = range(variant.position, variant.position + len(variant.reference_allele))
    lookup = {position: index for index, position in enumerate(positions)}
    if not all(position in lookup for position in affected):
        raise ValueError("Variant crosses a coding boundary; protein consequence is unsupported")
    indices = sorted(lookup[position] for position in affected)
    if indices != list(range(indices[0], indices[0] + len(indices))):
        raise ValueError("Variant does not map to contiguous coding bases")
    ref, alt = variant.reference_allele, variant.alternate_allele
    if TRANSCRIPT_METADATA[variant.gene]["strand"] == -1:
        ref, alt = ucsc_service.reverse_complement(ref), ucsc_service.reverse_complement(alt)
        logger.info('Transcript-oriented alleles: {}>{} -> {}>{}', variant.reference_allele,
                    variant.alternate_allele or '<deletion>', ref, alt or '<deletion>')
    index = indices[0]
    altered = replace_allele(reference["cds"], index, ref, alt)
    protein = translate_cds(altered)
    logger.info('Altered CDS created at CDS position {} (1-based): {} bp -> {} bp; translated={} aa',
                index + 1, len(reference['cds']), len(altered), len(protein))
    return altered, protein, index + 1
