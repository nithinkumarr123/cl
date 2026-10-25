!pip install fastapi uvicorn transformers torch pyngrok nest_asyncio httpx python-multipart

import torch
import nest_asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForMaskedLM, AutoTokenizer
import numpy as np
import torch.nn.functional as F
from pyngrok import ngrok
import uvicorn
import threading
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.colab import userdata

try:
    NGROK_AUTH_TOKEN = userdata.get('NGROK_AUTH_TOKEN')
    if NGROK_AUTH_TOKEN:
        !ngrok config add-authtoken {NGROK_AUTH_TOKEN}
        print("✅ ngrok authenticated")
    else:
        raise ValueError("No token")
except:
    print("⚠️ Please set up ngrok token in Colab secrets")
    print("1. Go to https://dashboard.ngrok.com/signup")
    print("2. Get your authtoken")
    print("3. Add to Colab secrets as NGROK_AUTH_TOKEN")

class DNARequest(BaseModel):
    ref: str
    alt: str
    pos: int

class DNAResponse(BaseModel):
    ref_pll: float
    alt_pll: float
    delta_score: float
    interpretation: str

class ProteinRequest(BaseModel):
    sequence: str
    position: int
    ref_aa: str
    alt_aa: str
    altered_sequence: str | None = None

class ProteinResponse(BaseModel):
    ref_score: float
    alt_score: float
    delta_score: float
    impact: str

print("\n📦 Loading models...")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

print("Loading Nucleotide Transformer...")
nt_model_name = "InstaDeepAI/nucleotide-transformer-500m-human-ref"
nt_model = AutoModelForMaskedLM.from_pretrained(nt_model_name).to(device)
nt_tokenizer = AutoTokenizer.from_pretrained(nt_model_name)
nt_model.eval()
print("✅ Nucleotide Transformer loaded")

print("Loading ESM-2...")
esm_model_name = "facebook/esm2_t33_650M_UR50D"
esm_model = AutoModelForMaskedLM.from_pretrained(esm_model_name).to(device)
esm_tokenizer = AutoTokenizer.from_pretrained(esm_model_name)
esm_model.eval()
print("✅ ESM-2 loaded")

def compute_dna_pll(sequence: str) -> float:
    tokens = nt_tokenizer(sequence, return_tensors='pt', truncation=False)
    if not sequence or len(sequence) >= 6000 or tokens['input_ids'].shape[1] > 1000:
        raise ValueError("DNA must be nonempty, below 6000 bases and at most 1000 tokens")
    input_ids = tokens['input_ids'][0]
    with torch.no_grad():
        outputs = nt_model(**{k: v.to(device) for k, v in tokens.items()})
        logits = outputs.logits[0]
    log_probs = F.log_softmax(logits, dim=-1)
    token_probs = log_probs[range(len(input_ids)), input_ids]
    return token_probs.mean().item()

def score_dna_variant(ref_seq: str, alt_seq: str, pos: int) -> dict:
    if not 0 <= pos < len(ref_seq):
        raise ValueError("DNA position is outside the reference window")
    ref_window = ref_seq
    alt_window = alt_seq
    ref_pll = compute_dna_pll(ref_window)
    alt_pll = compute_dna_pll(alt_window)
    delta = alt_pll - ref_pll
    if delta < -0.5:
        interpretation = "disruptive"
    elif abs(delta) <= 0.5:
        interpretation = "neutral"
    else:
        interpretation = "tolerated"
    return {
        "ref_pll": ref_pll,
        "alt_pll": alt_pll,
        "delta_score": delta,
        "interpretation": interpretation
    }

def score_protein_mutation(sequence: str, position: int, ref_aa: str, alt_aa: str) -> dict:
    amino_acids = set("ACDEFGHIKLMNPQRSTVWY")
    if ref_aa not in amino_acids or alt_aa not in amino_acids:
        raise ValueError("ESM scoring requires standard amino-acid substitutions")
    if not sequence or not set(sequence) <= amino_acids:
        raise ValueError("Protein window contains unsupported residues")
    tokens = esm_tokenizer(sequence, return_tensors='pt', truncation=False)
    if tokens['input_ids'].shape[1] > 512:
        raise ValueError("Protein window exceeds 512 tokens")
    tokens = {k: v.to(device) for k, v in tokens.items()}
    if not 1 <= position <= len(sequence) or sequence[position - 1] != ref_aa:
        raise ValueError("Protein reference residue/position mismatch")
    tokens['input_ids'][0, position] = esm_tokenizer.mask_token_id
    with torch.no_grad():
        outputs = esm_model(**tokens)
        logits = outputs.logits[0]
    pos_idx = position
    if pos_idx < len(logits):
        log_probs = F.log_softmax(logits[pos_idx], dim=-1)
        ref_token = esm_tokenizer.convert_tokens_to_ids(ref_aa)
        alt_token = esm_tokenizer.convert_tokens_to_ids(alt_aa)
        ref_score = log_probs[ref_token].item() if ref_token != esm_tokenizer.unk_token_id else -5.0
        alt_score = log_probs[alt_token].item() if alt_token != esm_tokenizer.unk_token_id else -5.0
        delta = alt_score - ref_score
        if delta < -2:
            impact = "deleterious"
        elif delta < -0.5:
            impact = "probably_damaging"
        elif delta > 1:
            impact = "benign"
        else:
            impact = "tolerated"
        return {
            "ref_score": ref_score,
            "alt_score": alt_score,
            "delta_score": delta,
            "impact": impact
        }
    return {
        "ref_score": 0.0,
        "alt_score": 0.0,
        "delta_score": 0.0,
        "impact": "unknown"
    }

app = FastAPI(title="ML Inference Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_ngrok_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models": ["nucleotide_transformer", "esm2"]}

@app.post("/score_dna", response_model=DNAResponse)
async def score_dna(request: DNARequest):
    try:
        result = score_dna_variant(request.ref, request.alt, request.pos)
        return DNAResponse(**result)
    except Exception as e:
        logger.error(f"DNA scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score_protein", response_model=ProteinResponse)
async def score_protein(request: ProteinRequest):
    try:
        if request.altered_sequence is not None:
            expected = (request.sequence[:request.position - 1] + request.alt_aa
                        + request.sequence[request.position:])
            if request.altered_sequence != expected:
                raise ValueError("Only single amino-acid substitutions are supported")
        result = score_protein_mutation(
            request.sequence, request.position, request.ref_aa, request.alt_aa
        )
        return ProteinResponse(**result)
    except Exception as e:
        logger.error(f"Protein scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

print("\n🚀 Starting FastAPI server...")

nest_asyncio.apply()

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(3)

print("🔗 Creating ngrok tunnel...")
ngrok.kill()
public_url = ngrok.connect(8000)

url_str = str(public_url).replace("NgrokTunnel: ", "").split(" ->")[0].strip('"')

print(f"\n{'='*60}")
print("🎉 ML SERVER IS RUNNING!")
print(f"{'='*60}")
print(f"📍 Public URL: {url_str}")
print(f"📍 Health check: {url_str}/health")
print(f"📍 DNA scoring: {url_str}/score_dna")
print(f"📍 Protein scoring: {url_str}/score_protein")
print(f"{'='*60}")
print(f"\n📝 COPY THIS URL to your .env file:")
print(f"COLAB_API_URL={url_str}")
