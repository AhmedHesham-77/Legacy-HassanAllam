FROM python:3.11.9
WORKDIR /appspace
COPY appspace_players/image/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*
EXPOSE 56437
CMD ["python3", "appspace_players/main.py"]