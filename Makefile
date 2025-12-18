PY ?= python
LOOKBACK_DAYS ?= 3650

.PHONY: run_all run_one report lint format smoke

run_all:
	$(PY) -m macrolens_poc.cli run-all --lookback-days $(LOOKBACK_DAYS)

run_one:
	@if [ -z "$(ID)" ]; then \
		echo "Usage: make run_one ID=<series_id> [LOOKBACK_DAYS=3650]"; \
		exit 1; \
	fi
	$(PY) -m macrolens_poc.cli run-one --id $(ID) --lookback-days $(LOOKBACK_DAYS)

report:
	$(PY) -m macrolens_poc.cli report

lint:
	$(PY) -m ruff check src tests

format:
	$(PY) -m ruff format src tests

smoke:
	$(PY) -m pytest -q
