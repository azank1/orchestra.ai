FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY .env.template .env

CMD ["uvicorn", "src.orchestra.main:app", "--host", "0.0.0.0", "--port", "8000"]
