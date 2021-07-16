FROM python:3-alpine

COPY ./requirements.txt ./requirements.txt

COPY ./entrypoint.sh ./entrypoint.sh
RUN ["chmod", "+x", "entrypoint.sh"]

RUN pip3 install -r ./requirements.txt

COPY . .

ENTRYPOINT ["./entrypoint.sh", "${API_PORT}" ]