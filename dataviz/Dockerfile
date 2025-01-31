FROM python:3.10

WORKDIR /app/utils
COPY utils/requirements.txt .
WORKDIR /app
COPY dataviz/requirements.txt .

RUN pip install --no-cache-dir virtualenv && \
    virtualenv venv && \
    /bin/bash -c "source venv/bin/activate && pip install --no-cache-dir -r requirements.txt" && \
    /bin/bash -c "source venv/bin/activate && pip install --no-cache-dir -r utils/requirements.txt"

COPY utils/*.py ./utils
COPY dataviz/*.py .

EXPOSE 8050

CMD ["/bin/bash", "-c", "source venv/bin/activate && python main.py"]
