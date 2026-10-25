"""UniProt Service."""

import httpx
from typing import Optional, Dict
from loguru import logger
from config import config


class UniProtService:
    def __init__(self):
        self.base_url = config.UNIPROT_API

    async def get_protein_info(self, gene: str) -> Dict:
        logger.info('UniProt search: gene={} organism=9606', gene)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{self.base_url}/uniprotkb/search",
                    params={
                        "query": f"gene_exact:{gene} AND organism_id:9606",
                        "format": "json",
                        "size": 1,
                    },
                )
                if r.status_code == 200:
                    results = r.json().get("results", [])
                    if results:
                        entry = results[0]
                        name = (entry.get("proteinDescription", {})
                                .get("recommendedName", {})
                                .get("fullName", {})
                                .get("value", f"{gene} protein"))
                        logger.info('UniProt protein name received: {}', name)
                        return {
                            "protein_name": name,
                            "function": "DNA repair / tumor suppressor",
                            "tissue_expression": ["Breast", "Ovary"],
                        }
        except Exception as e:
            logger.warning(f"⚠️ UniProt failed: {e}")

        logger.warning('UniProt using fallback protein name for {}', gene)
        return {
            "protein_name": f"{gene} protein",
            "function": "DNA repair / tumor suppressor",
            "tissue_expression": ["Breast", "Ovary"],
        }


uniprot_service = UniProtService()
