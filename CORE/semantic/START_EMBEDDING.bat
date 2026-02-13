@echo off
echo Starting Semantic Memory Embedding Service...
echo.
echo If this fails, run: pip install sentence-transformers fastapi uvicorn
echo.
python embedding_service.py
pause
