# ---- Stage 1: build the React site ----
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python API + the built site, one container ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY --from=frontend /build/dist ./static
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
# Safe default: production mode (the server refuses to start with unsafe settings)
ENV ENV=production STATIC_DIR=/app/static
EXPOSE 10000
# Hosts such as Render provide the port in $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
