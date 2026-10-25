"""ACMG/AMP 2015 Table 5 combination of explicitly reviewed evidence.

This does not automatically curate criteria or implement all VCEP rules.
"""
from models.schemas import ACMGClassification as Category, ACMGResult

REFERENCES = ["https://pubmed.ncbi.nlm.nih.gov/25741868/",
              "https://cspec.genome.network/cspec/ui/svi/summary"]


class ACMGService:
    def assess(self, gene, review=None):
        warnings = [
            "Research evidence calculator; not a validated clinical classification service.",
            "Uses generic 2015 Table 5 combinations. Gene-specific criterion applicability, strength, "
            "dependencies and any alternative VCEP combining rules require expert review.",
            "DNA/ESM-2 scores and ClinVar assertions are not automatically assigned ACMG criteria.",
        ]
        if review is None:
            return ACMGResult(summary="ACMG assessment not performed: no reviewed evidence supplied.",
                              warnings=warnings, references=REFERENCES)
        criteria = review.criteria
        codes = {item.code for item in criteria}
        if {'PP3', 'BP4'} <= codes or {'PS3', 'BS3'} <= codes:
            raise ValueError("Opposing computational/functional criteria cannot be applied together")
        if {'PS2', 'PM6'} <= codes:
            raise ValueError("Confirmed and unconfirmed de novo evidence cannot be counted together")
        if gene == 'TP53' and 'PVS1' in codes:
            if 'PP3' in codes:
                raise ValueError("TP53 specifications prohibit combining PVS1 with PP3")
            if any(c.code == 'PVS1' and c.strength == 'very_strong' for c in criteria) and 'PS3' in codes:
                raise ValueError("TP53 full-strength PVS1 must not be combined with PS3")
        if not criteria:
            return ACMGResult(summary="Review supplied without assessed criteria; classification not performed.",
                              review=review, warnings=warnings, references=REFERENCES)
        def count(direction, strength):
            return sum(c.code.startswith(direction) and c.strength == strength for c in criteria)
        vs, strong, moderate, supporting = [count('P', level) for level in
                                            ('very_strong', 'strong', 'moderate', 'supporting')]
        bs, bp = count('B', 'strong'), count('B', 'supporting')
        pathogenic, likely_pathogenic, benign, likely_benign = [], [], [], []
        if vs and (strong or moderate >= 2 or (moderate and supporting) or supporting >= 2):
            pathogenic.append('P(i): very strong plus qualifying additional evidence')
        if strong >= 2:
            pathogenic.append('P(ii): at least two strong pathogenic criteria')
        if strong and (moderate >= 3 or (moderate >= 2 and supporting >= 2)
                       or (moderate >= 1 and supporting >= 4)):
            pathogenic.append('P(iii): strong plus qualifying moderate/supporting evidence')
        if vs and moderate:
            likely_pathogenic.append('LP(i): very strong plus moderate')
        if strong and moderate:
            likely_pathogenic.append('LP(ii): strong plus moderate')
        if strong and supporting >= 2:
            likely_pathogenic.append('LP(iii): strong plus two supporting')
        if moderate >= 3:
            likely_pathogenic.append('LP(iv): three moderate')
        if moderate >= 2 and supporting >= 2:
            likely_pathogenic.append('LP(v): two moderate plus two supporting')
        if moderate >= 1 and supporting >= 4:
            likely_pathogenic.append('LP(vi): moderate plus four supporting')
        if 'BA1' in codes:
            benign.append('B(i): stand-alone benign criterion')
        if bs >= 2:
            benign.append('B(ii): two strong benign criteria')
        if bs and bp:
            likely_benign.append('LB(i): strong plus supporting benign')
        if bp >= 2:
            likely_benign.append('LB(ii): two supporting benign')
        # Preserve contradictory evidence for review instead of cancelling it numerically.
        contradictory = any(c.code.startswith('P') for c in criteria) and any(c.code.startswith('B') for c in criteria)
        if contradictory:
            category, status = Category.VUS, 'conflicting_evidence'
            matched = ['VUS(ii): opposing pathogenic and benign evidence requires review']
        elif pathogenic:
            category, status, matched = Category.PATHOGENIC, 'calculated', pathogenic
        elif likely_pathogenic:
            category, status, matched = Category.LIKELY_PATHOGENIC, 'calculated', likely_pathogenic
        elif benign:
            category, status, matched = Category.BENIGN, 'calculated', benign
        elif likely_benign:
            category, status, matched = Category.LIKELY_BENIGN, 'calculated', likely_benign
        else:
            category, status, matched = Category.VUS, 'insufficient_evidence', ['VUS(i): no qualifying combination']
        return ACMGResult(classification=category, assessment_status=status,
            summary=f"{category.value} from supplied criteria for {review.condition}; requires expert review.",
            evidence={c.code: [c.strength, c.rationale, str(c.source_url)] for c in criteria},
            applied_criteria=criteria, matched_rules=matched, review=review,
            warnings=warnings, references=REFERENCES)


acmg_service = ACMGService()
