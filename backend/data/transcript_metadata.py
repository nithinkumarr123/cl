"""
RefSeq MANE Select transcript metadata for BRCA1 and TP53 (GRCh38/hg38).
Verified against Ensembl canonical transcripts:
  - BRCA1: ENST00000357654.9 (NM_007294.4 / NP_009225.1)
  - TP53:  ENST00000269305.9 (NM_000546.6 / NP_000537.3)
"""

TRANSCRIPT_METADATA = {
    "BRCA1": {
        "gene": "BRCA1",
        "refseq_mrna": "NM_007294.4",
        "refseq_protein": "NP_009225.1",
        "ensembl_transcript": "ENST00000357654",
        "chromosome": "17",
        "strand": -1,
        # CDS boundaries: 5' end = highest genomic coord (minus strand)
        "cds_start": 43124096,     # A of ATG (was 43125364 — that was transcript start)
        "cds_end":   43045678,     # last base of stop codon (was 43045703)
        "cds_length_bp": 5592,
        "protein_length_aa": 1863,
        "exons": [
            # 5'UTR — no coding
            {"start": 43125271, "end": 43125364},   # Exon 23 (5'UTR)
            # Coding exons (transcription order = high coord -> low coord)
            {"start": 43124017, "end": 43124115},   # Exon 22 (contains ATG)
            {"start": 43115726, "end": 43115779},   # Exon 21
            {"start": 43106456, "end": 43106533},   # Exon 20
            {"start": 43104868, "end": 43104956},   # Exon 19
            {"start": 43104122, "end": 43104261},   # Exon 18
            {"start": 43099775, "end": 43099880},   # Exon 17 (was 43099877)
            {"start": 43097244, "end": 43097289},   # Exon 16
            {"start": 43095846, "end": 43095922},   # Exon 15
            {"start": 43091435, "end": 43094860},   # Exon 14 (huge)
            {"start": 43090944, "end": 43091032},   # Exon 13
            {"start": 43082404, "end": 43082575},   # Exon 12 (was 43082572)
            {"start": 43076488, "end": 43076614},   # Exon 11
            {"start": 43074331, "end": 43074521},   # Exon 10
            {"start": 43070928, "end": 43071238},   # Exon 9
            {"start": 43067608, "end": 43067695},   # Exon 8
            {"start": 43063874, "end": 43063951},   # Exon 7
            {"start": 43063333, "end": 43063373},   # Exon 6
            {"start": 43057052, "end": 43057135},   # Exon 5
            {"start": 43051063, "end": 43051117},   # Exon 4
            {"start": 43049121, "end": 43049194},   # Exon 3
            {"start": 43047643, "end": 43047703},   # Exon 2
            {"start": 43044295, "end": 43045802},   # Exon 1 (3'UTR + stop codon)
        ],
    },
    "TP53": {
        "gene": "TP53",
        "refseq_mrna": "NM_000546.6",
        "refseq_protein": "NP_000537.3",
        "ensembl_transcript": "ENST00000269305",
        "chromosome": "17",
        "strand": -1,
        "cds_start": 7676594,      # A of ATG (was 7676622 — off by 28bp)
        "cds_end":   7669609,      # last base of stop codon (was 7668421 — way off)
        "cds_length_bp": 1182,
        "protein_length_aa": 393,
        "exons": [
            # 5'UTR — no coding
            {"start": 7687377, "end": 7687490},   # Exon 11 (5'UTR)
            # Coding exons (transcription order = high coord -> low coord)
            {"start": 7676521, "end": 7676622},   # Exon 10 (contains ATG)
            {"start": 7676382, "end": 7676403},   # Exon 9
            {"start": 7675994, "end": 7676272},   # Exon 8
            {"start": 7675053, "end": 7675236},   # Exon 7
            {"start": 7674859, "end": 7674971},   # Exon 6
            {"start": 7674181, "end": 7674290},   # Exon 5
            {"start": 7673701, "end": 7673837},   # Exon 4
            {"start": 7673535, "end": 7673608},   # Exon 3
            {"start": 7670609, "end": 7670715},   # Exon 2
            {"start": 7668421, "end": 7669690},   # Exon 1 (3'UTR past 7669609)
        ],
    },
}