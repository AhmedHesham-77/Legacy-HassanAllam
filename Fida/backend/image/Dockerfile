FROM python:3.11.9

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY image/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

EXPOSE 56242
# Command to run the application
CMD ["python3", "main.py"]