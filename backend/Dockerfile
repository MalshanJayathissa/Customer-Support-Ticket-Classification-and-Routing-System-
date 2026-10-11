FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PIP_DEFAULT_TIMEOUT=1000

LABEL org.opencontainers.image.source="https://github.com/MalshanJayathissa/Customer-Support-Ticket-Classification-and-Routing-System-"

COPY requirements.txt ./requirements.txt

# CPU-only PyTorch: avoids downloading large CUDA dependencies
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu torch && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY models ./models

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]