.PHONY: venv lint test check

venv:
	python3 -m venv .venv
	.venv/bin/pip install -q -r requirements-test.txt

lint:
	.venv/bin/ruff check . --exclude .venv
	.venv/bin/ruff format --check . --exclude .venv

test:
	.venv/bin/pytest -q

check: lint test
