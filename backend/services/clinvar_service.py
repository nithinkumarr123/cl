"""Exact hg38 allele matching against live ClinVar germline VCV records."""
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import httpx
from loguru import logger
from config import config
from models.schemas import ACMGClassification

CATEGORIES = {item.value.lower(): item.value for item in ACMGClassification}
CATEGORIES['uncertain significance'] = ACMGClassification.VUS.value


def minimal_allele(position, ref, alt):
    """Trim shared bases. Does not left-align repeat indels; unmatched variants stay unmatched."""
    ref, alt = ref.upper(), alt.upper()
    while ref and alt and ref[-1] == alt[-1]:
        ref, alt = ref[:-1], alt[:-1]
    while ref and alt and ref[0] == alt[0]:
        ref, alt, position = ref[1:], alt[1:], position + 1
    return position, ref, alt


def parse_exact_records(xml, gene, chrom, position, ref, alt):
    """Only single-allele, exact GRCh38 VCV matches; never select by significance substring."""
    root = ET.fromstring(xml)
    matches = {}
    target = minimal_allele(position, ref, alt)
    archives = [root] if root.tag == 'VariationArchive' else root.findall('.//VariationArchive')
    for archive in archives:
        allele = archive.find('./ClassifiedRecord/SimpleAllele')
        if allele is None:
            continue  # Haplotype/genotype assertions do not classify the single input allele.
        symbols = {g.get('Symbol') for g in allele.findall('./GeneList/Gene')}
        if gene not in symbols:
            continue
        exact = False
        for location in allele.findall('./Location/SequenceLocation'):
            if location.get('Assembly') != 'GRCh38' or location.get('Chr') != chrom.removeprefix('chr'):
                continue
            try:
                candidate = minimal_allele(int(location.attrib['positionVCF']),
                    location.attrib['referenceAlleleVCF'], location.attrib['alternateAlleleVCF'])
            except (KeyError, ValueError):
                continue
            if candidate == target:
                exact = True
                break
        if not exact:
            continue
        classification = archive.find('./ClassifiedRecord/Classifications/GermlineClassification')
        if classification is None:
            continue  # Somatic classifications are a different framework.
        description = classification.findtext('Description') or 'Not provided'
        review = classification.findtext('ReviewStatus') or 'Not provided'
        conditions = sorted({n.text for traits in classification.findall('./ConditionList/TraitSet')
                             if traits.get('ContributesToAggregateClassification') != 'false'
                             for n in traits.findall('./Trait/Name/ElementValue')
                             if n.text and n.get('Type') == 'Preferred'})
        variation_id = archive.get('VariationID')
        if not variation_id:
            continue
        matches[variation_id] = dict(clinical_significance=description,
            classification=CATEGORIES.get(description.strip().lower()),
            review_status=review, conditions=conditions, found=True, exact_match=True,
            lookup_status='matched', variation_id=variation_id,
            source_url=f'https://www.ncbi.nlm.nih.gov/clinvar/variation/{variation_id}/',
            last_evaluated=classification.get('DateLastEvaluated'))
    return list(matches.values())


class ClinVarService:
    def __init__(self):
        self.base_url = config.NCBI_API

    async def get_clinvar_for_variant(self, gene, ref, alt, position=None, chromosome='chr17', genome_build='GRCh38'):
        result = dict(clinical_significance='Not available', conditions=[], review_status='Not available',
                      found=False, exact_match=False, lookup_status='not_found',
                      retrieved_at=datetime.now(timezone.utc).isoformat())
        if position is None or genome_build != 'GRCh38':
            return {**result, 'lookup_status': 'unsupported', 'note': 'Only exact GRCh38 germline matches are supported.'}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                # Include allele span for anchored deletions; verify exact alleles in VCV XML afterwards.
                term = (f'{gene}[gene] AND {chromosome.removeprefix("chr")}[chr] AND '
                        f'{max(1, position - 1)}:{position + max(1, len(ref))}[chrpos38]')
                logger.info('ClinVar search: {} {}:{} {}>{} ({})', gene, chromosome,
                            position, ref, alt or '<deletion>', genome_build)
                search = await client.get(f'{self.base_url}/esearch.fcgi', params={
                    'db': 'clinvar', 'term': term, 'retmode': 'json', 'retmax': 100})
                search.raise_for_status()
                search_data = search.json()
                response = search_data.get('esearchresult', {})
                if search_data.get('error') or response.get('errorlist') or response.get('ERROR'):
                    raise ValueError('ClinVar search returned an API error')
                ids = response.get('idlist', [])
                logger.info('ClinVar candidates received: {}', len(ids))
                if not ids:
                    return {**result, 'note': 'No exact match found; absence from ClinVar does not imply benignity.'}
                # NCBI allows 3 requests/sec without an API key.
                import asyncio
                await asyncio.sleep(0.35)
                logger.info('ClinVar fetching {} VCV XML records for exact allele checking', len(ids))
                fetch = await client.get(f'{self.base_url}/efetch.fcgi', params={
                    'db': 'clinvar', 'id': ','.join(ids), 'rettype': 'vcv', 'retmode': 'xml', 'is_variationid': 'true'})
                fetch.raise_for_status()
                matches = parse_exact_records(fetch.text, gene, chromosome, position, ref, alt)
                logger.info('ClinVar exact germline matches: {}', len(matches))
                if len(matches) == 1:
                    matched = matches[0]
                    if 'conflict' in matched['clinical_significance'].lower():
                        matched['lookup_status'] = 'conflicting'
                    return {**result, **matched,
                        'note': 'External ClinVar germline assertion, not an ACMG calculation by this application. Review the condition and evidence at the source.'}
                if len(matches) > 1:
                    return {**result, 'lookup_status': 'ambiguous', 'note': 'Multiple exact records found; manual review required.'}
                return {**result, 'note': 'No exact allele match in returned records. Repeat indels are not left-aligned by this lookup.'}
        except (httpx.HTTPError, ValueError, ET.ParseError) as exc:
            logger.warning(f'ClinVar lookup unavailable: {exc}')
            return {**result, 'lookup_status': 'unavailable', 'note': 'ClinVar could not be queried; no database classification inferred.'}


clinvar_service = ClinVarService()
