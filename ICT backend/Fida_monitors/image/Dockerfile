FROM python:3.11.9
WORKDIR /fida
COPY Fida_monitors/image/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*
EXPOSE 56434
CMD ["python3", "Fida_monitors/main.py"]