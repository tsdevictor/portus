from pathlib import Path

from backend.detect_ai_apis import scan_file


def write_file(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content)
    return path


def providers(results):
    return {result.provider.lower() for result in results}


def test_scanner_detects_openai_import(tmp_path):
    path = write_file(
        tmp_path,
        "openai_example.py",
        """
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "hello"}],
)
""",
    )

    results = scan_file(path)

    assert "openai" in providers(results)


def test_scanner_detects_anthropic_import(tmp_path):
    path = write_file(
        tmp_path,
        "anthropic_example.py",
        """
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-5-sonnet-latest",
    max_tokens=100,
    messages=[{"role": "user", "content": "hello"}],
)
""",
    )

    results = scan_file(path)

    assert "anthropic" in providers(results)


def test_scanner_detects_gemini_import(tmp_path):
    path = write_file(
        tmp_path,
        "gemini_example.py",
        """
import google.generativeai as genai

model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("hello")
""",
    )

    results = scan_file(path)
    detected = providers(results)

    assert "google genai" in detected or "gemini" in detected or "google" in detected or "google-gemini" in detected


def test_scanner_ignores_false_positive_strings(tmp_path):
    path = write_file(
        tmp_path,
        "false_positive.py",
        '''
# This documentation mentions OpenAI and Anthropic, but does not call either API.
PROVIDERS = ["openai", "anthropic", "gemini"]

def explain():
    return "We may support openai later."
''',
    )

    results = scan_file(path)

    assert results == []
