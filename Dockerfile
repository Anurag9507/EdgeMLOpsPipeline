# Stage 1: Use an official Python image as the base
# Using 'slim' makes the image smaller
FROM python:3.11-slim

# Stage 2: Set the working directory inside the container
WORKDIR /app

# Install the GNU OpenMP library, a system dependency for lightgbm
RUN apt-get update && apt-get install -y libgomp1 curl && rm -rf /var/lib/apt/lists/*
# Stage 3: Copy and install dependencies
# This is done first to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 4: Copy the rest of the application code into the container
COPY . .

# The command to run the container will be specified in docker-compose.yml
# because this single image will be used for multiple services.