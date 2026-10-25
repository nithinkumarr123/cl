"""Illustrative impact bins; no ACMG criteria, database labels, or probabilities."""
import math
from models.schemas import VariantImpactResult


class VariantImpactService:
    def predict_impact(self, mutation_type, dna_score, protein_score):
        mtype = getattr(mutation_type, 'value', mutation_type)
        evidence = {}
        total = 0.0

        def usable(score):
            return score.status == 'scored' and math.isfinite(score.delta_score)

        if not usable(dna_score) or (mtype == 'missense' and not usable(protein_score)):
            return VariantImpactResult(status='not_scored',
                summary='Required model results are unavailable; no experimental impact category assigned.')
        if mtype in ('inframe_indel', 'stop_lost', 'start_lost'):
            return VariantImpactResult(status='unsupported',
                summary='This consequence is not supported by the experimental scoring rule.')

        def add(key, weight, explanation):
            nonlocal total
            total += weight
            evidence[key] = [explanation, f'Illustrative weight: {weight:+.1f}']

        # Retain the original prototype's positive weights with descriptive names.
        # Negative model bins make low/minimal outcomes reachable; these weights
        # are illustrative, not fitted or calibrated to clinical classifications.
        if mtype in ('frameshift', 'nonsense'):
            add('protein_truncating_consequence', 1.0, f'Predicted {mtype} sequence consequence')
        elif mtype == 'synonymous':
            add('unchanged_protein_sequence', -0.3, 'Translation is unchanged; splicing effects are not assessed')
        elif mtype == 'missense':
            delta = protein_score.delta_score
            if delta < -5.0:
                weight = 0.9
            elif delta < -2.0:
                weight = 0.6
            elif delta < -1.0:
                weight = 0.3
            elif delta >= 1.0:
                weight = -0.6
            else:
                weight = 0.0
            add('protein_model_prediction', weight, f'ESM-2 delta: {delta:.3f}')
        delta = dna_score.delta_score
        add('dna_model_prediction', 0.3 if delta < -0.5 else -0.6 if delta >= 0.5 else 0.0,
            f'Nucleotide Transformer delta: {delta:.3f}')
        total = round(total, 3)
        if total >= 1.0:
            category = 'High predicted impact'
        elif total >= 0.5:
            category = 'Moderate predicted impact'
        elif total <= -1.0:
            category = 'Minimal predicted impact'
        elif total <= -0.5:
            category = 'Low predicted impact'
        else:
            category = 'Uncertain predicted impact'
        return VariantImpactResult(status='scored', impact_score=total, predicted_impact=category,
            evidence=evidence, summary=f'{category} under illustrative heuristic-v1 thresholds. '
                'Requires further validation; a low prediction does not rule out a harmful effect.')


variant_impact_service = VariantImpactService()
