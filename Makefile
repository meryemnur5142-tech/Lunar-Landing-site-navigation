.PHONY: test test-unit test-integration lint clean

test:
	PYTHONPATH=. python -m pytest tests/ -v --tb=short

test-unit:
	PYTHONPATH=. python -m pytest tests/unit/ -v --tb=short

test-integration:
	PYTHONPATH=. python -m pytest tests/integration/ -v --tb=short

lint:
	python -m py_compile domain/**/*.py mission_intelligence/**/*.py data-platform/**/*.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
