FROM node:22-bookworm-slim AS frontend
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 SLIDE_MAKER_NO_ENV_CHECK=1 SLIDE_MAKER_NO_VERSION_CHECK=1 TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata TIKTOKEN_CACHE_DIR=/opt/tiktoken
RUN apt-get update && apt-get install -y --no-install-recommends git libreoffice-impress libreoffice-writer tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng fonts-noto-core fontconfig libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY app/ ./app/
RUN pip install --no-cache-dir .
RUN python -c "import tiktoken; tiktoken.get_encoding('o200k_base')"
COPY vendor/slides_maker.lock.json ./vendor/slides_maker.lock.json
COPY scripts/bootstrap_vendor.py ./scripts/bootstrap_vendor.py
RUN python scripts/bootstrap_vendor.py
COPY --from=frontend /web/dist ./frontend/dist
RUN useradd --create-home --uid 10001 maic && mkdir /app/data && chown -R maic:maic /app/data
USER maic
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
