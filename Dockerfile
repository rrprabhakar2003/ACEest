FROM python:3.11-slim

LABEL maintainer="ravi.ranjan@thesouledstore.com"
LABEL app="aceest-fitness"
LABEL version="3.0.0"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ACEest_Fitness.py .
COPY ACEest_Fitness_v1.py .
COPY ACEest_Fitness_v2.py .

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

ENV FLASK_APP=ACEest_Fitness.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["python", "ACEest_Fitness.py"]
