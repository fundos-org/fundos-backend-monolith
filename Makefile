dev:
	PYTHONPATH=src uvicorn src.main:app --host 0.0.0.0 --reload
