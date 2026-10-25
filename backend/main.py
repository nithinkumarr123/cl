from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from config import config
import sys
from time import perf_counter
from uuid import uuid4
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler, http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

logger.remove()
logger.configure(extra={'request_id': '-'})
logger.add(sys.stdout, level=config.LOG_LEVEL,
    format='{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | [{extra[request_id]}] {message}')

from models.schemas import *
from services.ml_client import ml_client
from services.variant_sequences import genomic_pair, coding_reference, coding_pair
from services.transcript_service import transcript_service
from services.clinvar_service import clinvar_service
from services.uniprot_service import uniprot_service
from services.acmg_service import acmg_service
from services.variant_impact_service import variant_impact_service
from data.transcript_metadata import TRANSCRIPT_METADATA
from utils.translation_utils import get_amino_acid_at_position

app = FastAPI(title=config.API_TITLE, version=config.API_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
_cds_cache = {}


@app.middleware('http')
async def log_requests(request, call_next):
    started = perf_counter()
    with logger.contextualize(request_id=uuid4().hex[:8]):
        # Health polling stays concise; analyses receive a full progress trace.
        log = logger.debug if request.url.path == '/health' else logger.info
        log('REQUEST {} {}', request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception('REQUEST FAILED {} {} after {:.2f}s', request.method,
                             request.url.path, perf_counter() - started)
            raise
        log('RESPONSE {} {} -> HTTP {} in {:.2f}s', request.method, request.url.path,
            response.status_code, perf_counter() - started)
        return response


@app.exception_handler(RequestValidationError)
async def log_validation_error(request, exc):
    for error in exc.errors():
        logger.warning('HTTP 422 validation error: {}: {}',
                       '.'.join(str(part) for part in error['loc']), error['msg'])
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(StarletteHTTPException)
async def log_http_error(request, exc):
    log = logger.error if exc.status_code >= 500 else logger.warning
    log('HTTP {} {} {}: {}', exc.status_code, request.method, request.url.path, exc.detail)
    return await http_exception_handler(request, exc)


async def get_gene_sequences(gene):
    if gene not in _cds_cache:
        logger.info('CDS cache MISS for {}; fetching coding exon portions', gene)
        _cds_cache[gene] = await coding_reference(gene)
    else:
        logger.info('CDS cache HIT for {}; reusing {} bp / {} aa', gene,
                    len(_cds_cache[gene]['cds']), len(_cds_cache[gene]['protein']))
    return _cds_cache[gene]


def protein_fragment(protein, position):
    index = position - 1
    if not 0 <= index < len(protein):
        return protein[max(0, index - 10):index] + "[STOP]"
    return protein[max(0, index - 10):index] + "[" + protein[index] + "]" + protein[index + 1:index + 11]


@app.post("/analyze", response_model=AnalysisOutput)
async def analyze_variant(variant: VariantInput):
    logger.info('ANALYSIS {} {}:{} {}>{} assembly={}', variant.gene, variant.chromosome,
                variant.position, variant.reference_allele, variant.alternate_allele or '<deletion>',
                variant.genome_build.value)
    meta = TRANSCRIPT_METADATA.get(variant.gene)
    if not meta:
        raise HTTPException(422, "Only BRCA1 and TP53 are supported")
    if variant.genome_build != GenomeBuild.HG38:
        raise HTTPException(422, "Only GRCh38/hg38 is supported by the transcript annotations")
    if variant.chromosome != "chr" + meta["chromosome"]:
        raise HTTPException(422, "Chromosome does not match the selected gene")
    logger.info('Input accepted; transcript={} strand={}', meta['refseq_mrna'], meta['strand'])
    try:
        acmg = acmg_service.assess(variant.gene, variant.acmg_review)
        acmg.variant = variant.model_dump(mode='json', exclude={'acmg_review'})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    mapped = await transcript_service.map_variant(variant.gene, variant.position,
                variant.reference_allele, variant.alternate_allele)
    if not mapped:
        raise HTTPException(422, "Position is outside the selected gene")
    logger.info('Transcript mapping: status={} CDS_position={} AA_position={}',
                mapped['status'], mapped.get('cds_position'), mapped.get('aa_position'))
    try:
        ref_dna, alt_dna, local_position, window_start = await genomic_pair(variant)
        reference = await get_gene_sequences(variant.gene)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
    try:
        dna = await ml_client.score_dna(ref_dna, alt_dna, local_position)
        if dna.get("interpretation") in ("error", "not_configured"):
            raise RuntimeError("DNA model unavailable or not configured")
        dna_score = DNAScore(**dna, status="scored", sequence_length=len(ref_dna),
                             altered_sequence_length=len(alt_dna), window_start=window_start)
        logger.info('DNA score: ref={} alt={} delta={:.6f} interpretation={}', dna_score.ref_pll,
                    dna_score.alt_pll, dna_score.delta_score, dna_score.interpretation)
    except Exception as exc:
        raise HTTPException(502, f"DNA scoring failed: {exc}") from exc

    coding = mapped["status"] == "coding"
    cds_pos, aa_pos = None, None
    ref_aa, alt_aa = "?", "?"
    alt_cds, alt_protein = reference["cds"], reference["protein"]
    protein_score = ProteinScore(impact="not_applicable", status="not_applicable")
    mtype = MutationType.INTRONIC if mapped["status"] == "intronic" else MutationType.UTR
    if coding:
        try:
            alt_cds, alt_protein, cds_pos = coding_pair(reference, variant)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        aa_pos = (cds_pos - 1) // 3 + 1
        ref_aa = get_amino_acid_at_position(reference["cds"], cds_pos)
        alt_aa = get_amino_acid_at_position(alt_cds, cds_pos) if cds_pos + (3 - (cds_pos - 1) % 3) - 1 <= len(alt_cds) else "*"
        length_change = len(alt_cds) - len(reference["cds"])
        if length_change % 3:
            mtype = MutationType.FRAMESHIFT
        elif length_change:
            mtype = MutationType.INFRAME
        elif ref_aa == "*" and alt_aa != "*":
            mtype = MutationType.STOP_LOST
        elif reference["cds"].startswith("ATG") and not alt_cds.startswith("ATG"):
            mtype = MutationType.START_LOST
        elif len(alt_protein) < len(reference["protein"]):
            mtype = MutationType.NONSENSE
        elif alt_protein == reference["protein"]:
            mtype = MutationType.SYNONYMOUS
        else:
            mtype = MutationType.MISSENSE
        logger.info('Protein consequence: {} CDS_position={} AA={}{}>{}; ref={} aa alt={} aa',
                    mtype.value, cds_pos, ref_aa, aa_pos, alt_aa,
                    len(reference['protein']), len(alt_protein))
        # ESM substitution likelihood is supported only for a single changed residue.
        changes = [i for i, (a, b) in enumerate(zip(reference["protein"], alt_protein)) if a != b]
        if (mtype == MutationType.MISSENSE and len(alt_protein) == len(reference["protein"])
                and len(changes) == 1):
            index = changes[0]
            start, end = max(0, index - 100), min(len(alt_protein), index + 101)
            try:
                result = await ml_client.score_protein(reference["protein"][start:end],
                    index - start + 1, reference["protein"][index], alt_protein[index],
                    alt_protein[start:end])
                status = "error" if result.get("impact") in ("error", "not_configured") else "scored"
                protein_score = ProteinScore(**result, status=status)
                logger.info('ESM-2 score: status={} delta={:.6f} impact={}',
                            status, protein_score.delta_score, protein_score.impact)
            except Exception as exc:
                logger.error(f"Protein scoring failed: {exc}")
                protein_score = ProteinScore(impact="error", status="error")
        elif mtype == MutationType.SYNONYMOUS:
            protein_score = ProteinScore(impact="unchanged_protein", status="not_applicable")
            logger.info('ESM-2 skipped: synonymous variant; translated protein unchanged')
        else:
            protein_score = ProteinScore(impact="unsupported_variant_type", status="unsupported")
            logger.info('ESM-2 skipped: consequence {} is unsupported for substitution scoring', mtype.value)

    if not coding:
        logger.info('Protein alteration/scoring skipped: variant status={}', mapped['status'])

    logger.info('Fetching external ClinVar germline annotation')
    clinvar = await clinvar_service.get_clinvar_for_variant(variant.gene,
        variant.reference_allele, variant.alternate_allele, variant.position)
    logger.info('ClinVar result: status={} exact_match={} classification={}',
                clinvar.get('lookup_status', 'unknown'), clinvar.get('exact_match', False),
                clinvar.get('clinical_significance', 'Not available'))
    logger.info('Fetching UniProt annotation for {}', variant.gene)
    uniprot = await uniprot_service.get_protein_info(variant.gene)
    impact = variant_impact_service.predict_impact(mtype, dna_score, protein_score)
    logger.info('Experimental impact: method={} status={} score={} category={}',
                impact.method_version, impact.status, impact.impact_score, impact.predicted_impact)
    for signal, details in impact.evidence.items():
        logger.info('Impact contribution {}: {}', signal, '; '.join(details))
    # Raw language-model scores are not calibrated clinical evidence.
    return AnalysisOutput(
        variant=variant.model_dump(),
        transcript=TranscriptInfo(transcript_id=reference["transcript_id"], gene_symbol=variant.gene,
            cds_sequence=reference["cds"], protein_sequence=reference["protein"],
            altered_cds_sequence=alt_cds if coding else None,
            altered_protein_sequence=alt_protein if coding else None,
            variant_in_cds=coding, cds_position=cds_pos, aa_position=aa_pos,
            source=reference["source"], status=mapped["status"]),
        dna_score=dna_score,
        protein_analysis=ProteinAnalysis(mutation_type=mtype, ref_aa=ref_aa, alt_aa=alt_aa,
            aa_position=aa_pos or 0, protein_score=protein_score,
            ref_fragment=protein_fragment(reference["protein"], aa_pos) if coding else "",
            alt_fragment=protein_fragment(alt_protein, aa_pos) if coding else ""),
        uniprot=UniProtInfo(**uniprot), clinvar=ClinVarInfo(
            **{k: v for k, v in clinvar.items() if k != 'clinical_significance'},
            significance=clinvar.get("clinical_significance", "Not available")), acmg=acmg,
        experimental_impact=impact)


@app.post("/acmg/assess", response_model=ACMGResult)
async def assess_acmg(variant: VariantInput):
    if variant.gene not in TRANSCRIPT_METADATA or variant.chromosome != 'chr17' or variant.genome_build != GenomeBuild.HG38:
        raise HTTPException(422, 'Only BRCA1/TP53 on chr17 GRCh38 are supported')
    try:
        assessment = acmg_service.assess(variant.gene, variant.acmg_review)
        assessment.variant = variant.model_dump(mode='json', exclude={'acmg_review'})
        return assessment
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post('/clinvar/lookup', response_model=ClinVarInfo)
async def lookup_clinvar(variant: VariantInput):
    if variant.gene not in TRANSCRIPT_METADATA or variant.chromosome != 'chr17' or variant.genome_build != GenomeBuild.HG38:
        raise HTTPException(422, 'Only BRCA1/TP53 on chr17 GRCh38 are supported')
    if not variant.reference_allele or variant.reference_allele == variant.alternate_allele:
        raise HTTPException(422, 'Supply a nonempty REF and a different ALT')
    record = await clinvar_service.get_clinvar_for_variant(variant.gene, variant.reference_allele,
        variant.alternate_allele, variant.position)
    return ClinVarInfo(**{k: v for k, v in record.items() if k != 'clinical_significance'},
                       significance=record.get('clinical_significance', 'Not available'))


@app.get("/health")
async def health():
    return {"status": "ok", "version": config.API_VERSION, "ml_server": await ml_client.health_check()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
