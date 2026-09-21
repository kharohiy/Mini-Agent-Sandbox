FROM python:3.11-slim

WORKDIR /app
COPY requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt
# .dockerignore prevents local state and legacy vault material entering this image.
COPY api.py capability_policy.py capabilities.json sandbox_executor.py project_search.py project_registry.py knowledge_store.py ./
RUN useradd --system --uid 10001 --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
