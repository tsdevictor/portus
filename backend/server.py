"""
FastAPI server wrapping detect_ai_apis.py for the Portus frontend.

Start with:
    python3 server.py
    # or
    uvicorn server:app --port 8000 --reload
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import logic from detect_ai_apis
sys.path.insert(0, str(Path(__file__).parent))
from detect_ai_apis import (
    scan_file,
    detect_backends,
    analyze_with_mistral,
    suggest_models,
    BackendType,
)

app = FastAPI(title="Portus API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FALLBACK_JSON = Path(__file__).parent / "models_sample.json"


@app.get("/api/health")
def health():
    backend = detect_backends("ollama")
    return {
        "status": "ok",
        "backends": {
            "ollama": backend.ollama_available,
            "hf": backend.hf_available,
            "active": backend.active.value,
        },
        "warning": backend.warning or None,
    }


@app.post("/api/scan")
async def scan(
    files: list[UploadFile] = File(...),
    paths: list[str] = Form(default=[]),   # relative paths for directory uploads
    backend: str = Form(default="auto"),
    no_mistral: bool = Form(default=False),
    hf_token: Optional[str] = Form(default=None),
    context_lines: int = Form(default=20),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    tmpdir = Path(tempfile.mkdtemp(prefix="portus_"))
    try:
        # Write uploaded files into temp directory, preserving relative paths
        written: list[Path] = []
        for i, upload in enumerate(files):
            rel = paths[i] if i < len(paths) else upload.filename or f"file_{i}"
            dest = tmpdir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = await upload.read()
            dest.write_bytes(content)
            written.append(dest)

        # Determine scan target
        target = tmpdir if len(written) > 1 else written[0]

        # Backend detection
        backend_status = detect_backends(backend, hf_token)
        if no_mistral:
            backend_status.active = BackendType.NONE

        # Collect file extensions present
        extensions = list({f.suffix.lstrip(".") for f in written if f.suffix})
        if not extensions:
            extensions = ["py"]

        # Scan
        from detect_ai_apis import collect_files
        scan_files = collect_files(target, extensions) if target.is_dir() else [target]

        all_results = []
        for fpath in scan_files:
            detections = scan_file(fpath, context_lines)
            for det in detections:
                analysis = None
                suggestions = []
                if backend_status.active != BackendType.NONE:
                    analysis = analyze_with_mistral(det, backend_status, hf_token)
                if analysis:
                    suggestions = suggest_models(analysis.hf_pipeline_tag, FALLBACK_JSON)

                # Make file path relative for the response
                try:
                    rel_file = str(Path(det.file).relative_to(tmpdir))
                except ValueError:
                    rel_file = det.file

                all_results.append({
                    "file": rel_file,
                    "line_number": det.line_number,
                    "provider": det.provider,
                    "method": det.method,
                    "detection_type": det.detection_type,
                    "context_snippet": det.context_snippet,
                    "analysis": {
                        "task_description": analysis.task_description,
                        "hf_pipeline_tag": analysis.hf_pipeline_tag,
                        "confidence": analysis.confidence,
                    } if analysis else None,
                    "suggestions": [
                        {
                            "id": s.id,
                            "task": s.task,
                            "downloads": s.downloads,
                            "likes": s.likes,
                            "description": s.description,
                            "source": s.source,
                        }
                        for s in suggestions
                    ],
                })

        return {
            "total_detections": len(all_results),
            "files_scanned": len(scan_files),
            "backend_used": backend_status.active.value,
            "detections": all_results,
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
