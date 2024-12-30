FROM python:3.11.9
WORKDIR /analysis
COPY postgres/image/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*
CMD ["python3", "postgres/main.py"]