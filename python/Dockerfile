FROM python:3.10.6-alpine

RUN addgroup -S mercari && adduser -S trainee -G mercari


# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create Directory
RUN mkdir -p /app/db \
    && mkdir -p /app/images 

# Copy the remaining file into the container
COPY db .
COPY main.py .
COPY images .

# Change the ownership of the directory
RUN chown -R trainee:mercari /app/db \
    && chown -R trainee:mercari /app/images 

# Switch to the trainee user
USER trainee

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
