import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


class Config:
    PROJECT_ROOT = Path(__file__).parent

    COLAB_API_URL = os.getenv("COLAB_API_URL", "")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    API_TITLE = "ClinX Clinical - Variant Interpretation System"
    API_VERSION = "4.0.0"
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    NCBI_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    UNIPROT_API = "https://rest.uniprot.org"

    GENE_ALIASES = {
        'BRCA1': 'BRCA1',
        'BRCA2': 'BRCA2',
        'TP53': 'TP53',
        'P53': 'TP53',
    }


config = Config()
