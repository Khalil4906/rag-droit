.PHONY: init dev ui test lint ingest clean

init:
	python scripts/init_db.py

dev:
	uvicorn app.main:app --reload --port 8000

ui:
	streamlit run streamlit/app.py

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/
	ruff format app/ tests/

ingest:
	python scripts/ingest_batch.py ./data/raw

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +