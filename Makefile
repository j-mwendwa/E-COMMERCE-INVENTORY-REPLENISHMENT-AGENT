.PHONY: install dev test lint format eval serve ingest seed clean

install:
	pip install -e ".[dev,eval]"
	pre-commit install

dev:
	uvicorn src.api.main:app --reload --port 8000

serve:
	uvicorn src.api.main:app --port 8000

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest -m integration -v

lint:
	ruff check src/
	mypy src/

format:
	ruff check src/ --fix
	ruff format src/

eval:
	python evals/run_evals.py

ingest:
	python scripts/ingest_suppliers.py

seed:
	python scripts/seed_data.py

clean:
	rm -rf data/checkpoints/*.db data/memory/*.json chroma/
