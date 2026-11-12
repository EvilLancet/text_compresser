FROM python:3.12


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY static ./static

ENV DATABASE_URL=sqlite:////data/sqlite3.db
ENV LLM_URL=http://llm_service:8001

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]