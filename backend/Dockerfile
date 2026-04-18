FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements.txt /tmp/backend-requirements.txt
COPY ai_engine/requirements.txt /tmp/ai-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio \
    && pip install --no-cache-dir -r /tmp/ai-requirements.txt

COPY backend /app/backend
COPY ai_engine /app/ai_engine

RUN mkdir -p /app/backend/uploads

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

