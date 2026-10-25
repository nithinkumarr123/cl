"""Persistent UCSC exon records, indexed by assembly and genomic coordinates."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

BACKUP_DIR = Path(__file__).resolve().parents[1] / "data" / "exon_backups"


def save_exon(gene, transcript, chrom, start, end, sequence, directory=BACKUP_DIR):
    sequence = sequence.upper()
    if len(sequence) != end - start or not set(sequence) <= set("ACGTN"):
        raise ValueError("Invalid exon sequence length or alphabet")
    record = dict(gene=gene, transcript_id=transcript, genome="hg38", chromosome=chrom,
                  start=start, end=end, coordinates="0-based-half-open", strand="genomic_plus",
                  source="https://api.genome.ucsc.edu", downloaded_at=datetime.now(timezone.utc).isoformat(),
                  sha256=hashlib.sha256(sequence.encode()).hexdigest(), dna=sequence)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{gene}_hg38_{chrom}_{start}_{end}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    logger.info('Exon backup saved: {} ({} bp)', path.name, len(sequence))


def load_region(chrom, start, end, genome, directory=BACKUP_DIR):
    if start < 0 or end <= start:
        return None
    for path in directory.glob(f"*_{genome}_{chrom}_*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            dna = record["dna"]
            if (record["genome"] != genome or record["chromosome"] != chrom
                    or record["coordinates"] != "0-based-half-open"
                    or record["strand"] != "genomic_plus"
                    or len(dna) != record["end"] - record["start"]
                    or not set(dna) <= set("ACGTN")
                    or hashlib.sha256(dna.encode()).hexdigest() != record["sha256"]):
                continue
            if record["start"] <= start < end <= record["end"]:
                logger.info('Exon backup matched: {}; requested slice={}:{}; {} bp',
                            path.name, start - record['start'], end - record['start'], end - start)
                return dna[start - record["start"]:end - record["start"]]
        except (ValueError, KeyError, TypeError, OSError):
            continue
    return None
