FROM python:3-alpine

RUN addgroup --gid 1024 bbgroup
RUN adduser --disabled-password --gecos "" --force-badname --ingroup 1024 bbuser 
USER bbuser

COPY ./requirements.txt ./requirements.txt

COPY ./entrypoint.sh ./entrypoint.sh
RUN ["chmod", "+x", "entrypoint.sh"]

RUN pip3 install -r ./requirements.txt

COPY . .

ENTRYPOINT ["./entrypoint.sh", "${API_PORT}" ]