FROM ubuntu:21.04

RUN apt-get update && apt-get install -y \
        software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-pip
RUN python3.7 -m pip install pip
RUN apt-get update && apt-get install -y \
    python3-distutils \
    python3-setuptools
RUN python3.7 -m pip install pip --upgrade pip

RUN apt-get install python3.7-dev -y


COPY requirements.txt requirements.txt

RUN python3.7 -m pip install -r ./requirements.txt

COPY . .

RUN ["chmod", "+x", "entrypoint.sh"]

ENTRYPOINT ["./entrypoint.sh", "${API_PORT}" ]

#FROM python:3-alpine

#RUN apk add --no-cache git

#COPY requirements.txt requirements.txt

#RUN pip3 install -r ./requirements.txt

#COPY . .

#RUN ["chmod", "+x", "entrypoint.sh"]

#ENTRYPOINT ["./entrypoint.sh", "${API_PORT}" ]