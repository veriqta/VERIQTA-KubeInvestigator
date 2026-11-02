.PHONY: setup preflight test check run demo clean
PYTHON ?= python3
VENV ?= .venv
setup:
	$(PYTHON) -c 'import sys; sys.exit("Python 3.12+ is required; use make setup PYTHON=python3.12") if sys.version_info < (3, 12) else None'
	$(PYTHON) src/kubeinvestigator/sqlite_runtime.py
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip==26.2.2
	$(VENV)/bin/pip install -r requirements-dev.lock
	$(VENV)/bin/pip install --no-deps --no-build-isolation -e .
preflight:
	$(VENV)/bin/python -m kubeinvestigator.sqlite_runtime
test: preflight
	$(VENV)/bin/pytest -q
check:
	$(VENV)/bin/ruff check src tests scripts
	$(VENV)/bin/ruff format --check src tests scripts
	$(VENV)/bin/mypy src
	$(VENV)/bin/python scripts/check_docs.py
run: preflight
	$(VENV)/bin/uvicorn kubeinvestigator.app:create_app --factory --host 127.0.0.1 --port 8080 --no-access-log
demo:
	bash scripts/demo.sh setup
clean:
	bash scripts/demo.sh cleanup
