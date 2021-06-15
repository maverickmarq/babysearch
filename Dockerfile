FROM python:3-alpine

COPY . .

RUN pip3 install -r ./requirements.txt
RUN ["chmod", "+x", "entrypoint.sh"]

ENTRYPOINT ["./entrypoint.sh", "${API_PORT}" ]