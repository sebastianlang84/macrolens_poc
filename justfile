set shell := ["bash", "-c"]

py := env("PY", default="python")
default_lookback := "3650"

run_all lookback_days=default_lookback:
    {{py}} -m macrolens_poc.cli run-all --lookback-days {{lookback_days}}

run_one id lookback_days=default_lookback:
    {{py}} -m macrolens_poc.cli run-one --id {{id}} --lookback-days {{lookback_days}}

report:
    {{py}} -m macrolens_poc.cli report

lint:
    {{py}} -m ruff check src tests

format:
    {{py}} -m black src tests

smoke:
    {{py}} -m pytest -q
