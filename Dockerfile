FROM apify/actor-python:3.11

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . ./

CMD ["python", "-u", "extrator.py"]