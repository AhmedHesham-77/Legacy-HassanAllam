FROM python:3.11.9
WORKDIR /Qsys
COPY Qsys_systems/image/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*
EXPOSE 56436
CMD ["python3", "Qsys_systems/main.py"]