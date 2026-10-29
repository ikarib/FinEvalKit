FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
ENV DEMO_MODE=true
EXPOSE 8000
CMD ["uvicorn", "risk_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
