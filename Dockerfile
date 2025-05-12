# Use Python 3.12 as base image
FROM python:3.12-slim

# Install Node.js, npm and PostgreSQL
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    postgresql \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Initialize PostgreSQL
RUN service postgresql start && \
    su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'postgres';\"" && \
    su - postgres -c "createdb steambay"

# Expose ports
EXPOSE 8000 3000

# The command will be provided by docker-compose
CMD ["bash"] 