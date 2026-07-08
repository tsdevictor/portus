.PHONY: backend frontend test build

backend:
	cd backend && python -m uvicorn server:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	pytest backend/tests -q

build:
	cd frontend && npm run build
