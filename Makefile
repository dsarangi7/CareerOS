.PHONY: setup format lint typecheck test test-unit test-integration test-e2e migrate seed run-api run-dashboard validate export-demo export-profile export-profile-csv import-jobs docker-up

setup:
	python -m scripts.tasks setup

format:
	python -m ruff format .

lint:
	python -m ruff check .

typecheck:
	python -m mypy app scripts tests

test:
	python -m pytest

test-unit:
	python -m pytest tests/unit

test-integration:
	python -m pytest tests/integration

test-e2e:
	python -m pytest tests/end_to_end

migrate:
	python -m scripts.tasks migrate

seed:
	python -m scripts.tasks seed

run-api:
	python -m uvicorn app.api.main:app --reload

run-dashboard:
	python -m streamlit run dashboard/Home.py

validate:
	python -m scripts.tasks validate

export-demo:
	python -m scripts.tasks export-demo

export-profile:
	python -m scripts.tasks export-profile

export-profile-csv:
	python -m scripts.tasks export-profile-csv

import-jobs:
	python -m scripts.tasks import-jobs --path $(path)

docker-up:
	docker compose up --build
