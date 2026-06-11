import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Add V3 directory to path to import askhole
V3_DIR = Path(__file__).parent
sys.path.insert(0, str(V3_DIR))

from askhole import generate_report, get_vertical_econ

app = FastAPI(title="AskHole API")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class AskRequest(BaseModel):
    target: str
    vertical: str
    context: str = ""

@app.get("/")
def health():
    return {"status": "ok", "message": "AskHole API ready"}

@app.post("/generate")
def generate(req: AskRequest):
    try:
        econ = get_vertical_econ(req.vertical)
        report = generate_report(req.target, req.vertical, None, econ, req.context)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
