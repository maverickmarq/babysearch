FROM python:3-alpine

RUN apk add --no-cache git

COPY requirements.txt requirements.txt
RUN pip3 install -r ./requirements.txt

COPY . .

RUN ["chmod", "+x", "entrypoint.sh"]

ENTRYPOINT ["./entrypoint.sh", "${API_PORT}" ]