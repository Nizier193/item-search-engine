FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY item_search/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# System deps for OCR/pdf if needed (optional):
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Expose port
EXPOSE 8000

CMD ["uvicorn", "item_search.app.main:app", "--host", "0.0.0.0", "--port", "8000"]


