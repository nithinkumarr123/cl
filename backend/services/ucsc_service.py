"""UCSC Service - Fetch DNA sequences from UCSC REST API."""

import httpx
from typing import Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from services.exon_backup import load_region
from time import perf_counter


class UCSCService:
    def __init__(self):
        self.base_url = "https://api.genome.ucsc.edu"
        self.default_genome = "hg38"
        self.timeout = 20.0

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def fetch_region(self, chromosome: str, start: int, end: int,
                           genome: str = None) -> Optional[str]:
        """
        Fetch DNA for [start, end) using UCSC 0-based half-open coords.
        """
        genome = genome or self.default_genome
        chrom = chromosome if chromosome.startswith("chr") else f"chr{chromosome}"
        url = (f"{self.base_url}/getData/sequence"
               f"?genome={genome};chrom={chrom};start={start};end={end}")
        started = perf_counter()
        logger.info('UCSC fetch: {}:{}-{} ({})', chrom, start, end, genome)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(url)
                r.raise_for_status()
                seq = r.json().get("dna")
                if not seq:
                    raise ValueError("UCSC returned empty sequence")
                if len(seq) != end - start or not set(seq.upper()) <= set("ACGTN"):
                    raise ValueError("UCSC returned invalid sequence")
                logger.info('UCSC received: {} bp; HTTP {}; {:.2f}s', len(seq), r.status_code,
                            perf_counter() - started)
                return seq.upper()
        except Exception as e:
            logger.error(f"❌ UCSC fetch failed: {e}")
            saved = load_region(chrom, start, end, genome)
            if saved:
                logger.warning(f"Using exon backup: {genome} {chrom}:{start}-{end}")
            else:
                logger.error('No matching exon backup for {} {}:{}-{}', genome, chrom, start, end)
            return saved

    @staticmethod
    def reverse_complement(seq: str) -> str:
        """Reverse-complement a DNA sequence."""
        return seq.translate(str.maketrans("ACGT", "TGCA"))[::-1]


# Singleton
ucsc_service = UCSCService()
