# Use an official Python runtime as a parent image
FROM python:3.11.5

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app, prompts, and scrapy-project directories into the container
COPY app /app/app
COPY prompts /app/prompts
COPY scrapy-project /app/scrapy-project

# Copy other necessary files such as .env and any log files you need
COPY .env error_logs.log /app/

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
