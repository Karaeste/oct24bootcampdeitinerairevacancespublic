FROM python:3.10-slim

WORKDIR /app/utils
COPY utils/requirements.txt .
WORKDIR /app
COPY api/requirements.txt .

RUN pip install --no-cache-dir virtualenv && \
    virtualenv venv && \
    /bin/bash -c "source venv/bin/activate && pip install --no-cache-dir -r requirements.txt" && \
    /bin/bash -c "source venv/bin/activate && pip install --no-cache-dir -r utils/requirements.txt"

COPY ./utils/*.py ./utils/
COPY ./api/*.py ./
COPY ./api/demo/* ./demo/

EXPOSE 5000

CMD ["/bin/bash", "-c", "source venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 5000"]

