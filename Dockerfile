FROM apify/actor-python:latest

# Use a consistent working directory inside the container
WORKDIR /usr/src/app

# Install Python dependencies first (better Docker layer caching)
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY . ./

# Run the Actor (unbuffered logs for Apify)
CMD ["python", "-u", "extrator.py"]