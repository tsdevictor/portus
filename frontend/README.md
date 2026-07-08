# Frontend

React/TypeScript frontend for Hugging Face Search.

## Run locally

```bash
npm install
npm run dev
```

By default, the frontend expects the backend at:

```text
http://localhost:8000
```

## Main flow

1. User uploads a Python, JavaScript, or TypeScript codebase.
2. The frontend sends files to the FastAPI backend.
3. The backend scans for commercial AI API usage.
4. Results display detected providers, code context, inferred task, and suggested open-source Hugging Face replacements.
