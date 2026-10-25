from typing import Tuple

CODON_TABLE = {
    'ATA': 'I', 'ATC': 'I', 'ATT': 'I', 'ATG': 'M',
    'ACA': 'T', 'ACC': 'T', 'ACG': 'T', 'ACT': 'T',
    'AAC': 'N', 'AAT': 'N', 'AAA': 'K', 'AAG': 'K',
    'AGC': 'S', 'AGT': 'S', 'AGA': 'R', 'AGG': 'R',
    'CTA': 'L', 'CTC': 'L', 'CTG': 'L', 'CTT': 'L',
    'CCA': 'P', 'CCC': 'P', 'CCG': 'P', 'CCT': 'P',
    'CAC': 'H', 'CAT': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'CGA': 'R', 'CGC': 'R', 'CGG': 'R', 'CGT': 'R',
    'GTA': 'V', 'GTC': 'V', 'GTG': 'V', 'GTT': 'V',
    'GCA': 'A', 'GCC': 'A', 'GCG': 'A', 'GCT': 'A',
    'GAC': 'D', 'GAT': 'D', 'GAA': 'E', 'GAG': 'E',
    'GGA': 'G', 'GGC': 'G', 'GGG': 'G', 'GGT': 'G',
    'TCA': 'S', 'TCC': 'S', 'TCG': 'S', 'TCT': 'S',
    'TTC': 'F', 'TTT': 'F', 'TTA': 'L', 'TTG': 'L',
    'TAC': 'Y', 'TAT': 'Y', 'TAA': '*', 'TAG': '*',
    'TGC': 'C', 'TGT': 'C', 'TGA': '*', 'TGG': 'W',
}

def translate_codon(codon: str) -> str:
    if len(codon) != 3:
        raise ValueError(f"Invalid codon length: {codon} (length: {len(codon)})")
    if codon not in CODON_TABLE:
        raise KeyError(f"Codon not found in table: {codon}")
    return CODON_TABLE[codon]

def translate_cds(cds_seq: str) -> str:
    protein = []
    for i in range(0, len(cds_seq) - 2, 3):
        codon = cds_seq[i:i+3]
        if len(codon) == 3:
            try:
                aa = translate_codon(codon)
                if aa == '*':
                    break
                protein.append(aa)
            except KeyError:
                protein.append('?')
    return ''.join(protein)

def get_codon_at_position(cds_seq: str, cds_position: int) -> Tuple[str, int]:
    idx = cds_position - 1
    codon_start = (idx // 3) * 3
    codon_end = codon_start + 3
    if codon_end > len(cds_seq):
        raise ValueError(f"Position {cds_position} is beyond CDS length {len(cds_seq)}")
    codon = cds_seq[codon_start:codon_end]
    return codon, codon_start

def get_amino_acid_at_position(cds_seq: str, cds_position: int) -> str:
    codon, _ = get_codon_at_position(cds_seq, cds_position)
    return translate_codon(codon)