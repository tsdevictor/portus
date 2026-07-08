"""
detect_ai_apis.py — Scan source files for commercial AI API calls and suggest HuggingFace replacements.

Usage:
    python3 detect_ai_apis.py <file_or_dir> [options]
    python3 detect_ai_apis.py --help
"""

import ast
import re
import json
import ssl
import sys
import time
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from datetime import datetime

# ─────────────────────────────────────────────
# SSL context (macOS cert fix, same as sample_models.py)
# ─────────────────────────────────────────────
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ─────────────────────────────────────────────
# Detection patterns
# ─────────────────────────────────────────────

PROVIDER_IMPORTS = {
    "openai":               "OpenAI",
    "anthropic":            "Anthropic",
    "cohere":               "Cohere",
    "google.generativeai":  "Google GenAI",
    "mistralai":            "Mistral (commercial)",
    "boto3":                "AWS (boto3)",          # special — only flag if bedrock-runtime used
    "azure":                "Azure OpenAI",
}

# Dotted suffix -> (provider, human label)
API_CALL_PATTERNS: dict[str, tuple[str, str]] = {
    "chat.completions.create":      ("OpenAI",               "Chat Completion"),
    "completions.create":           ("OpenAI/Anthropic",     "Completion"),
    "embeddings.create":            ("OpenAI",               "Embedding"),
    "images.generate":              ("OpenAI",               "Image Generation"),
    "fine_tuning.jobs.create":      ("OpenAI",               "Fine-tuning"),
    "messages.create":              ("Anthropic",            "Messages API"),
    "messages.stream":              ("Anthropic",            "Messages Stream"),
    "co.generate":                  ("Cohere",               "Generate"),
    "co.embed":                     ("Cohere",               "Embed"),
    "co.classify":                  ("Cohere",               "Classify"),
    "co.summarize":                 ("Cohere",               "Summarize"),
    "co.chat":                      ("Cohere",               "Chat"),
    "generate_content":             ("Google GenAI",         "Generate Content"),
    "GenerativeModel":              ("Google GenAI",         "Model Init"),
    "count_tokens":                 ("Google GenAI",         "Count Tokens"),
    "AzureOpenAI":                  ("Azure OpenAI",         "Client Init"),
    "MistralClient":                ("Mistral (commercial)", "Client Init"),
    "Mistral":                      ("Mistral (commercial)", "Client Init"),
}

REGEX_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, provider, method_label)
    # Python imports
    (r'\bimport\s+openai\b',                        "OpenAI",               "import"),
    (r'from\s+openai\s+import',                     "OpenAI",               "import"),
    (r'\bimport\s+anthropic\b',                     "Anthropic",            "import"),
    (r'from\s+anthropic\s+import',                  "Anthropic",            "import"),
    (r'\bimport\s+cohere\b',                        "Cohere",               "import"),
    (r'from\s+cohere\s+import',                     "Cohere",               "import"),
    (r'import\s+google\.generativeai',              "Google GenAI",         "import"),
    (r'from\s+google\s+import\s+generativeai',      "Google GenAI",         "import"),
    (r'from\s+mistralai\b',                         "Mistral (commercial)", "import"),
    (r'\bimport\s+mistralai\b',                     "Mistral (commercial)", "import"),
    (r'AzureOpenAI\s*\(',                           "Azure OpenAI",         "AzureOpenAI"),
    (r'boto3\s*\.\s*client\s*\(\s*["\']bedrock',   "AWS Bedrock",          "bedrock-runtime"),
    (r'bedrock[-_]runtime',                         "AWS Bedrock",          "bedrock-runtime"),
    # API calls
    (r'\.chat\.completions\.create\s*\(',           "OpenAI",               "chat.completions.create"),
    (r'\.embeddings\.create\s*\(',                  "OpenAI",               "embeddings.create"),
    (r'\.images\.generate\s*\(',                    "OpenAI",               "images.generate"),
    (r'\.messages\.create\s*\(',                    "Anthropic",            "messages.create"),
    (r'\.messages\.stream\s*\(',                    "Anthropic",            "messages.stream"),
    (r'\bco\.generate\s*\(',                        "Cohere",               "co.generate"),
    (r'\bco\.embed\s*\(',                           "Cohere",               "co.embed"),
    (r'\bco\.classify\s*\(',                        "Cohere",               "co.classify"),
    (r'\.generate_content\s*\(',                    "Google GenAI",         "generate_content"),
    (r'genai\.GenerativeModel\s*\(',                "Google GenAI",         "GenerativeModel"),
    (r'MistralClient\s*\(',                         "Mistral (commercial)", "MistralClient"),
    # JS / TS
    (r'require\s*\(\s*["\']openai["\']\s*\)',       "OpenAI",               "require"),
    (r'from\s+["\']openai["\']',                    "OpenAI",               "import"),
    (r'from\s+["\']@anthropic-ai/sdk["\']',         "Anthropic",            "import"),
    (r'from\s+["\']@google/generative-ai["\']',     "Google GenAI",         "import"),
    (r'from\s+["\']cohere-ai["\']',                 "Cohere",               "import"),
    (r'from\s+["\']@mistralai/mistralai["\']',      "Mistral (commercial)", "import"),
    (r'require\s*\(\s*["\']@anthropic-ai/sdk["\']\s*\)', "Anthropic",       "require"),
]

KNOWN_HF_TASKS = {
    "any-to-any", "audio-classification", "audio-to-audio", "audio-text-to-text",
    "automatic-speech-recognition", "depth-estimation", "document-question-answering",
    "visual-document-retrieval", "feature-extraction", "fill-mask",
    "image-classification", "image-feature-extraction", "image-segmentation",
    "image-to-image", "image-text-to-text", "image-text-to-image", "image-text-to-video",
    "image-to-text", "image-to-video", "keypoint-detection", "mask-generation",
    "object-detection", "video-classification", "question-answering",
    "reinforcement-learning", "sentence-similarity", "summarization",
    "table-question-answering", "tabular-classification", "tabular-regression",
    "text-classification", "text-generation", "text-ranking", "text-to-image",
    "text-to-speech", "text-to-video", "token-classification", "translation",
    "unconditional-image-generation", "video-text-to-text", "video-to-video",
    "visual-question-answering", "zero-shot-classification",
    "zero-shot-image-classification", "zero-shot-object-detection",
    "text-to-3d", "image-to-3d",
}

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", ".tox", "dist", "build"}

# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class Detection:
    file: str
    line_number: int
    provider: str
    method: str
    detection_type: str       # "import" | "api_call"
    context_snippet: str

@dataclass
class Analysis:
    task_description: str
    hf_pipeline_tag: str
    confidence: str           # "high" | "medium" | "low"
    raw_response: str = ""

@dataclass
class ModelSuggestion:
    id: str
    task: str
    downloads: int
    likes: int
    description: str
    source: str               # "live_api" | "local_cache"

@dataclass
class ReportEntry:
    detection: Detection
    analysis: Optional[Analysis]
    suggestions: list[ModelSuggestion] = field(default_factory=list)

class BackendType(Enum):
    OLLAMA = "ollama"
    HF = "hf"
    NONE = "none"

@dataclass
class BackendStatus:
    active: BackendType
    ollama_available: bool
    hf_available: bool
    warning: str = ""

# ─────────────────────────────────────────────
# Backend detection
# ─────────────────────────────────────────────

def detect_backends(preferred: str, hf_token: Optional[str] = None) -> BackendStatus:
    ollama_ok = False
    hf_ok = False
    warning_parts = []

    # Check ollama
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            if "mistral" in result.stdout.lower():
                ollama_ok = True
            else:
                warning_parts.append(
                    "ollama found but mistral model not pulled — run: ollama pull mistral"
                )
    except FileNotFoundError:
        warning_parts.append(
            "ollama not installed — install with: brew install ollama && ollama pull mistral"
        )
    except subprocess.TimeoutExpired:
        warning_parts.append("ollama timed out during check")

    # Check huggingface_hub
    try:
        from huggingface_hub import InferenceClient  # noqa: F401
        hf_ok = True
    except ImportError:
        warning_parts.append(
            "huggingface_hub not installed — install with: pip install huggingface_hub"
        )

    # Determine active backend
    if preferred == "ollama":
        active = BackendType.OLLAMA if ollama_ok else BackendType.NONE
        if not ollama_ok:
            warning_parts.append("--backend ollama requested but ollama/mistral not ready")
    elif preferred == "hf":
        active = BackendType.HF if hf_ok else BackendType.NONE
        if not hf_ok:
            warning_parts.append("--backend hf requested but huggingface_hub not installed")
    else:  # auto
        if ollama_ok:
            active = BackendType.OLLAMA
        elif hf_ok:
            active = BackendType.HF
        else:
            active = BackendType.NONE

    return BackendStatus(
        active=active,
        ollama_available=ollama_ok,
        hf_available=hf_ok,
        warning="; ".join(warning_parts),
    )

# ─────────────────────────────────────────────
# File collection
# ─────────────────────────────────────────────

def collect_files(target: Path, extensions: list[str]) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lstrip(".") in extensions else []

    files = []
    for ext in extensions:
        for path in target.rglob(f"*.{ext}"):
            if not any(skip in path.parts for skip in SKIP_DIRS):
                files.append(path)
    return sorted(files)

# ─────────────────────────────────────────────
# AST helpers
# ─────────────────────────────────────────────

def flatten_attr(node) -> str:
    """Recursively flatten ast.Attribute chains into a dotted string."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = flatten_attr(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""

def extract_context(lines: list[str], line_number: int, context_lines: int) -> str:
    half = context_lines // 2
    start = max(0, line_number - 1 - half)
    end = min(len(lines), line_number + half)
    return "\n".join(f"{start + i + 1:4}: {lines[start + i]}" for i in range(end - start))

# ─────────────────────────────────────────────
# Static scanner
# ─────────────────────────────────────────────

def scan_file(path: Path, context_lines: int = 20) -> list[Detection]:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    lines = source.splitlines()
    detections: list[Detection] = []
    seen: set[tuple[int, str]] = set()  # (line, provider) — one detection per line per provider

    def add(line_no: int, provider: str, method: str, dtype: str):
        key = (line_no, provider)
        if key not in seen:
            seen.add(key)
            detections.append(Detection(
                file=str(path),
                line_number=line_no,
                provider=provider,
                method=method,
                detection_type=dtype,
                context_snippet=extract_context(lines, line_no, context_lines),
            ))

    # Pass A — AST (Python only)
    if path.suffix == ".py":
        try:
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                # Import detection
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod = ""
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            mod = alias.name
                            for key, prov in PROVIDER_IMPORTS.items():
                                if mod == key or mod.startswith(key + "."):
                                    if key != "boto3":  # boto3 handled separately
                                        add(node.lineno, prov, "import", "import")
                    else:
                        mod = node.module or ""
                        for key, prov in PROVIDER_IMPORTS.items():
                            if mod == key or mod.startswith(key + "."):
                                if key != "boto3":
                                    add(node.lineno, prov, "import", "import")

                # Call detection
                elif isinstance(node, ast.Call):
                    chain = flatten_attr(node.func)
                    for suffix, (prov, label) in API_CALL_PATTERNS.items():
                        if chain == suffix or chain.endswith("." + suffix):
                            add(node.lineno, prov, label, "api_call")
                            break
        except SyntaxError:
            pass  # fall through to regex

    # Pass B — Regex (all languages)
    for pattern, provider, method in REGEX_PATTERNS:
        for m in re.finditer(pattern, source, re.MULTILINE):
            line_no = source[:m.start()].count("\n") + 1
            dtype = "import" if method == "import" or method == "require" else "api_call"
            add(line_no, provider, method, dtype)

    # Deduplication: remove import-only detections when api_call exists for same provider
    providers_with_calls = {d.provider for d in detections if d.detection_type == "api_call"}
    detections = [
        d for d in detections
        if d.detection_type == "api_call" or d.provider not in providers_with_calls
    ]

    return sorted(detections, key=lambda d: d.line_number)

# ─────────────────────────────────────────────
# Mistral analysis
# ─────────────────────────────────────────────

ANALYSIS_PROMPT = """\
You are a code analyst. A source file contains a call to a commercial AI API.

Provider: {provider}
Method: {method}

Code context:
```
{snippet}
```

Based on the code context, determine what ML task this API call is performing.
Reply with ONLY valid JSON, no explanation, no markdown:
{{"task_description": "<one sentence describing what this code does>", "hf_pipeline_tag": "<one of the HuggingFace pipeline tags such as text-generation, summarization, text-classification, translation, question-answering, sentence-similarity, token-classification, fill-mask, text-to-image, image-to-text, image-classification, object-detection, automatic-speech-recognition, text-to-speech, feature-extraction, zero-shot-classification, or another valid HuggingFace pipeline tag>", "confidence": "<high|medium|low>"}}
"""

def _extract_json(text: str) -> dict:
    """Try to extract a JSON object from Mistral response text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'\{[^{}]*"task_description"[^{}]*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}

def _validate_tag(tag: str) -> str:
    if tag in KNOWN_HF_TASKS:
        return tag
    # fuzzy: check if any known tag is contained in or contains the response
    tag_lower = tag.lower().replace(" ", "-")
    for known in KNOWN_HF_TASKS:
        if known in tag_lower or tag_lower in known:
            return known
    return "text-generation"

def analyze_with_mistral(detection: Detection, backend: BackendStatus, hf_token: Optional[str] = None) -> Optional[Analysis]:
    prompt = ANALYSIS_PROMPT.format(
        provider=detection.provider,
        method=detection.method,
        snippet=detection.context_snippet,
    )

    raw = ""
    try:
        if backend.active == BackendType.OLLAMA:
            raw = _call_ollama(prompt)
        elif backend.active == BackendType.HF:
            raw = _call_hf(prompt, hf_token)
        else:
            return None
    except Exception as e:
        return Analysis(
            task_description=f"Analysis failed: {e}",
            hf_pipeline_tag="text-generation",
            confidence="low",
            raw_response=str(e),
        )

    parsed = _extract_json(raw)
    if not parsed:
        return Analysis(
            task_description="Could not parse Mistral response.",
            hf_pipeline_tag="text-generation",
            confidence="low",
            raw_response=raw[:300],
        )

    return Analysis(
        task_description=parsed.get("task_description", "Unknown"),
        hf_pipeline_tag=_validate_tag(parsed.get("hf_pipeline_tag", "text-generation")),
        confidence=parsed.get("confidence", "low"),
        raw_response=raw[:300],
    )

def _call_ollama(prompt: str) -> str:
    body = json.dumps({"model": "mistral", "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read())
    return data.get("response", "")

def _call_hf(prompt: str, token: Optional[str] = None) -> str:
    from huggingface_hub import InferenceClient
    client = InferenceClient(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        token=token,
    )
    # Format as instruction
    formatted = f"[INST] {prompt} [/INST]"
    for attempt in range(2):
        try:
            return client.text_generation(
                formatted,
                max_new_tokens=300,
                temperature=0.1,
                do_sample=False,
            )
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                time.sleep(3)
                continue
            raise
    return ""

# ─────────────────────────────────────────────
# HF model suggestions
# ─────────────────────────────────────────────

def suggest_models(pipeline_tag: str, fallback_json: Optional[Path]) -> list[ModelSuggestion]:
    # Try live HF API first
    try:
        params = urllib.parse.urlencode({
            "pipeline_tag": pipeline_tag,
            "sort": "downloads",
            "limit": 5,
            "full": "false",
        })
        url = f"https://huggingface.co/api/models?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "hfsearch/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            data = json.loads(resp.read())
        return [
            ModelSuggestion(
                id=m.get("id", ""),
                task=pipeline_tag,
                downloads=m.get("downloads", 0),
                likes=m.get("likes", 0),
                description=", ".join(m.get("tags", [])[:5]),
                source="live_api",
            )
            for m in data
        ]
    except Exception:
        pass

    # Fallback to local models_sample.json
    if fallback_json and fallback_json.exists():
        try:
            models = json.loads(fallback_json.read_text())
            filtered = [m for m in models if m.get("task") == pipeline_tag]
            filtered.sort(key=lambda m: m.get("downloads", 0), reverse=True)
            return [
                ModelSuggestion(
                    id=m["id"],
                    task=m.get("task", pipeline_tag),
                    downloads=m.get("downloads", 0),
                    likes=m.get("likes", 0),
                    description=m.get("description", ""),
                    source="local_cache",
                )
                for m in filtered[:5]
            ]
        except Exception:
            pass

    return []

# ─────────────────────────────────────────────
# Output / reporting
# ─────────────────────────────────────────────

W = 62

def _hr(char="─"):
    return char * W

def print_banner(backend: BackendStatus, target: Path, n_files: int):
    backend_label = {
        BackendType.OLLAMA: "ollama (local Mistral 7B)",
        BackendType.HF: "HuggingFace Inference API (Mistral-7B-Instruct)",
        BackendType.NONE: "NONE (detection only — no Mistral analysis)",
    }[backend.active]
    print()
    print(_hr("="))
    print("  detect_ai_apis.py — Commercial AI API Scanner")
    print(f"  Backend  : {backend_label}")
    print(f"  Target   : {target}")
    print(f"  Files    : {n_files}")
    print(_hr("="))
    if backend.warning:
        for w in backend.warning.split(";"):
            print(f"  [warn] {w.strip()}")
        print()

def print_entry(entry: ReportEntry, index: int, total: int, file_path: str):
    det = entry.detection
    ana = entry.analysis
    sug = entry.suggestions

    print(f"\n  Detection {index}/{total}")
    print(f"  {_hr()}")
    print(f"  Provider : {det.provider}")
    print(f"  Method   : {det.method}")
    print(f"  Location : line {det.line_number}")
    print(f"  Type     : {det.detection_type}")
    print(f"\n  Code context:")
    for ln in det.context_snippet.splitlines():
        print(f"    {ln}")

    if ana:
        conf_icon = {"high": "[high]", "medium": "[med] ", "low": "[low] "}.get(ana.confidence, "")
        print(f"\n  Mistral Analysis  {conf_icon}")
        print(f"  Task   : {ana.task_description}")
        print(f"  HF tag : {ana.hf_pipeline_tag}")

    if sug:
        src_note = f"(source: {sug[0].source})"
        print(f"\n  Suggested HuggingFace Replacements  {src_note}")
        for i, s in enumerate(sug, 1):
            dl = f"{s.downloads:,}" if s.downloads else "n/a"
            print(f"    {i}. {s.id}")
            print(f"       downloads: {dl}  likes: {s.likes}")
            if s.description:
                desc = s.description[:100] + "…" if len(s.description) > 100 else s.description
                print(f"       {desc}")
    elif ana:
        print(f"\n  No HuggingFace models found for task: {ana.hf_pipeline_tag}")

def print_summary(all_results: list[ReportEntry], n_files: int, output_path: Optional[Path]):
    providers: dict[str, int] = {}
    for r in all_results:
        providers[r.detection.provider] = providers.get(r.detection.provider, 0) + 1
    analyzed = sum(1 for r in all_results if r.analysis and r.analysis.confidence != "low" or
                   (r.analysis and r.analysis.task_description != "Could not parse Mistral response."))
    analyzed = sum(1 for r in all_results if r.analysis is not None)

    print(f"\n{_hr('=')}")
    print("  SUMMARY")
    print(f"  Files scanned    : {n_files}")
    print(f"  Detections found : {len(all_results)}")
    if providers:
        pstr = ", ".join(f"{p} ({c})" for p, c in sorted(providers.items()))
        print(f"  Providers found  : {pstr}")
    print(f"  Analyzed         : {analyzed}/{len(all_results)}")
    if output_path:
        print(f"  Report saved to  : {output_path}")
    print(_hr("="))
    print()

def write_json_report(all_results: list[ReportEntry], metadata: dict, output_path: Path):
    def ser(obj):
        if isinstance(obj, ReportEntry):
            return {
                "file": obj.detection.file,
                "line_number": obj.detection.line_number,
                "provider": obj.detection.provider,
                "method": obj.detection.method,
                "detection_type": obj.detection.detection_type,
                "context_snippet": obj.detection.context_snippet,
                "analysis": asdict(obj.analysis) if obj.analysis else None,
                "suggestions": [asdict(s) for s in obj.suggestions],
            }
        raise TypeError(f"Not serializable: {type(obj)}")

    report = {
        "scan_metadata": metadata,
        "detections": [ser(r) for r in all_results],
    }
    output_path.write_text(json.dumps(report, indent=2))

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Scan source files for commercial AI API calls and suggest HuggingFace replacements.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 detect_ai_apis.py my_script.py
  python3 detect_ai_apis.py ./my_project/ --output report.json
  python3 detect_ai_apis.py app.py --backend hf --hf-token hf_xxx
  python3 detect_ai_apis.py . --extensions py,js,ts --no-mistral
        """,
    )
    p.add_argument("target", type=Path, help="File or directory to scan")
    p.add_argument("--backend", choices=["ollama", "hf", "auto"], default="auto",
                   help="Mistral backend: ollama, hf, or auto (default: auto)")
    p.add_argument("--output", type=Path, metavar="PATH",
                   help="Write JSON report to this file")
    p.add_argument("--extensions", default="py",
                   help="Comma-separated file extensions to scan (default: py)")
    p.add_argument("--context-lines", type=int, default=20, metavar="N",
                   help="Lines of context to show per detection (default: 20)")
    p.add_argument("--no-mistral", action="store_true",
                   help="Skip Mistral analysis, detection only")
    p.add_argument("--hf-token", metavar="TOKEN",
                   help="HuggingFace token for higher rate limits")
    p.add_argument("--fallback-json", type=Path, metavar="PATH",
                   help="Path to models_sample.json for offline fallback")
    return p.parse_args()

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    args = parse_args()

    if not args.target.exists():
        print(f"Error: target '{args.target}' does not exist.", file=sys.stderr)
        sys.exit(1)

    extensions = [e.strip().lstrip(".") for e in args.extensions.split(",")]

    # Locate fallback JSON
    fallback_json = args.fallback_json
    if fallback_json is None:
        candidate = Path(__file__).parent / "models_sample.json"
        fallback_json = candidate if candidate.exists() else None
        if fallback_json is None:
            print("[warn] models_sample.json not found — offline fallback unavailable")

    # Backend detection
    backend = detect_backends(args.backend, args.hf_token)
    if args.no_mistral:
        backend.active = BackendType.NONE

    # Collect files
    files = collect_files(args.target, extensions)
    print_banner(backend, args.target, len(files))

    if not files:
        print("No matching files found.")
        return

    all_results: list[ReportEntry] = []

    for fpath in files:
        detections = scan_file(fpath, args.context_lines)
        if not detections:
            continue

        print(f"\n[{fpath}]  —  {len(detections)} detection(s)")

        file_det_count = len(detections)
        for idx, det in enumerate(detections, 1):
            analysis: Optional[Analysis] = None
            suggestions: list[ModelSuggestion] = []

            if backend.active != BackendType.NONE:
                print(f"  Analyzing detection {idx}/{file_det_count} with Mistral...", end=" ", flush=True)
                analysis = analyze_with_mistral(det, backend, args.hf_token)
                print("done" if analysis else "failed")
                if analysis and backend.active == BackendType.HF:
                    time.sleep(1)  # rate limit courtesy

            if analysis and analysis.hf_pipeline_tag:
                suggestions = suggest_models(analysis.hf_pipeline_tag, fallback_json)

            entry = ReportEntry(detection=det, analysis=analysis, suggestions=suggestions)
            all_results.append(entry)
            print_entry(entry, idx, file_det_count, str(fpath))

    if args.output:
        metadata = {
            "target": str(args.target),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "backend": backend.active.value,
            "files_scanned": len(files),
            "total_detections": len(all_results),
        }
        write_json_report(all_results, metadata, args.output)

    print_summary(all_results, len(files), args.output)


if __name__ == "__main__":
    main()
