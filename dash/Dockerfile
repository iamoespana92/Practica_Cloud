# Container image that runs your code
FROM python:3.10

# Copies your code file from your action repository to the filesystem path `/` of the container
# COPY practica.sh /practica.sh
# COPY practica.py /practica.py

COPY dash.py .
COPY requirements-dash.txt .

# RUN mkdir -p ~/.aws
# COPY config ~/.aws/config
# COPY credentials ~/.aws/credentials

# RUN apk update && apk add bash
# RUN apk add python3
# RUN apk add python3-dev
# RUN apk add gcc
# RUN apk add g++
# RUN apk add --no-cache musl-dev

RUN pip install -r requirements-dash.txt
#RUN pip3 install --no-cache-dir dash boto3 s3fs plotly 
# Code file to execute when the docker container starts up (`entrypoint.sh`)
CMD ["python", "./dash.py"]

