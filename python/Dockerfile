FROM python:3.10.6-alpine

RUN addgroup -S mercari && adduser -S trainee -G mercari


# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY python python

WORKDIR /app/python
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Change the ownership of the directory
RUN chown -R trainee:mercari /app/python/db \
    && chown -R trainee:mercari /app/python/images 

# Switch to the trainee user
USER trainee

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
