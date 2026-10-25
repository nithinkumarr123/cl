"""
Transcript Service - Maps genomic position to CDS/AA position.

Uses RefSeq exon structure and respects transcript strand.

Status values:
    coding  -> variant is inside a coding exon
    utr     -> variant is inside an exon but outside the CDS
    intronic -> variant is inside the gene span but not inside an exon
"""

from typing import Optional, Dict, Any
from loguru import logger

from data.transcript_metadata import TRANSCRIPT_METADATA


class RealTranscriptService:

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}

    async def map_variant(
        self,
        gene: str,
        position: int,
        ref: str,
        alt: str
    ) -> Optional[Dict[str, Any]]:

        # =========================================================
        # CACHE
        # =========================================================

        cache_key = f"{gene}_{position}_{ref}_{alt}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # =========================================================
        # GET TRANSCRIPT METADATA
        # =========================================================

        meta = TRANSCRIPT_METADATA.get(gene)

        if not meta:
            logger.error(f"❌ No metadata for {gene}")
            return None

        strand = meta["strand"]

        cds_start = meta["cds_start"]
        cds_end = meta["cds_end"]

        # Genomic CDS boundaries.
        # Works for both +1 and -1 strands.
        cds_lo = min(cds_start, cds_end)
        cds_hi = max(cds_start, cds_end)

        # =========================================================
        # GENE SPAN
        # =========================================================

        gene_lo = min(
            exon["start"]
            for exon in meta["exons"]
        )

        gene_hi = max(
            exon["end"]
            for exon in meta["exons"]
        )

        # =========================================================
        # STEP 1
        # CHECK WHETHER POSITION IS INSIDE ANY EXON
        #
        # IMPORTANT:
        # Do NOT clip the exon to CDS here.
        #
        # This lets us distinguish:
        #
        #   exon + CDS       -> coding
        #   exon + outside CDS -> UTR
        #   no exon          -> intronic
        # =========================================================

        containing_exon = None

        for exon in meta["exons"]:

            exon_start = exon["start"]
            exon_end = exon["end"]

            if exon_start <= position <= exon_end:
                containing_exon = exon
                break

        # =========================================================
        # STEP 2
        # POSITION IS INSIDE AN EXON
        # =========================================================

        if containing_exon is not None:

            # -----------------------------------------------------
            # 2A. EXON BUT OUTSIDE CDS
            #     This is UTR.
            # -----------------------------------------------------

            if not (cds_lo <= position <= cds_hi):

                result = {
                    "gene": gene,
                    "cds_position": None,
                    "aa_position": None,
                    "status": "utr",
                    "transcript_id": meta["refseq_mrna"],
                    "protein_id": meta["refseq_protein"],
                    "source": "refseq_exon_mapping",
                }

                self.cache[cache_key] = result

                logger.info(
                    f"ℹ️ {gene}:{position} is in exon but outside CDS (UTR)"
                )

                return result

        # =========================================================
        # STEP 3
        # POSITION IS IN A CODING EXON
        #
        # Sort exons in transcript direction.
        #
        # BRCA1 / TP53:
        # strand = -1
        #
        # Therefore transcript order is:
        # highest genomic coordinate -> lowest genomic coordinate
        # =========================================================

        sorted_exons = sorted(
            meta["exons"],
            key=lambda e: e["start"],
            reverse=(strand == -1)
        )

        cds_cursor = 0

        for exon in sorted_exons:

            exon_start = exon["start"]
            exon_end = exon["end"]

            # -----------------------------------------------------
            # Get only the coding portion of this exon.
            # -----------------------------------------------------

            coding_start = max(
                exon_start,
                cds_lo
            )

            coding_end = min(
                exon_end,
                cds_hi
            )

            # This exon contains no CDS bases.
            if coding_start > coding_end:
                continue

            coding_exon_length = (
                coding_end - coding_start + 1
            )

            # -----------------------------------------------------
            # Is the variant inside this coding portion?
            # -----------------------------------------------------

            if coding_start <= position <= coding_end:

                # -------------------------------------------------
                # Calculate offset within coding exon.
                #
                # For + strand:
                #
                # coding_start -> coding_end
                #
                # For - strand:
                #
                # coding_end -> coding_start
                #
                # because transcript direction is reversed.
                # -------------------------------------------------

                if strand == -1:

                    offset = (
                        coding_end
                        - position
                        + 1
                    )

                else:

                    offset = (
                        position
                        - coding_start
                        + 1
                    )

                # -------------------------------------------------
                # CDS position is 1-based.
                # -------------------------------------------------

                cds_position = (
                    cds_cursor
                    + offset
                )

                # -------------------------------------------------
                # Amino-acid position.
                #
                # CDS 1-3   -> AA 1
                # CDS 4-6   -> AA 2
                # CDS 7-9   -> AA 3
                # -------------------------------------------------

                aa_position = (
                    (cds_position - 1) // 3
                ) + 1

                result = {
                    "gene": gene,
                    "cds_position": cds_position,
                    "aa_position": aa_position,
                    "status": "coding",
                    "transcript_id": meta["refseq_mrna"],
                    "protein_id": meta["refseq_protein"],
                    "source": "refseq_exon_mapping",
                }

                self.cache[cache_key] = result

                logger.info(
                    f"✅ {gene}:{position} "
                    f"→ CDS {cds_position}, "
                    f"AA {aa_position}"
                )

                return result

            # -----------------------------------------------------
            # Move CDS cursor forward by this coding exon length.
            # -----------------------------------------------------

            cds_cursor += coding_exon_length

        # =========================================================
        # STEP 4
        # POSITION IS NOT IN ANY EXON
        #
        # If it is still inside the overall gene span, it is
        # intronic.
        # =========================================================

        if gene_lo <= position <= gene_hi:

            result = {
                "gene": gene,
                "cds_position": None,
                "aa_position": None,
                "status": "intronic",
                "transcript_id": meta["refseq_mrna"],
                "protein_id": meta["refseq_protein"],
                "source": "refseq_exon_mapping",
            }

            self.cache[cache_key] = result

            logger.warning(
                f"⚠️ {gene}:{position} is intronic"
            )

            return result

        # =========================================================
        # STEP 5
        # POSITION IS OUTSIDE THE GENE SPAN
        # =========================================================

        logger.error(
            f"❌ Position {position} outside {gene} span"
        )

        return None


# =============================================================
# SINGLE SERVICE INSTANCE
# =============================================================

transcript_service = RealTranscriptService()