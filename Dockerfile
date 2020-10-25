FROM selenium/standalone-chrome

RUN sudo apt-get update
RUN sudo apt-get install python3 python3-pip gunicorn3 -y

COPY requirements.txt requirements.txt

RUN pip3 install -r ./requirements.txt

COPY . .

RUN ["sudo", "chmod", "+x", "entrypoint.sh"]

ENTRYPOINT ["./entrypoint.sh", "${API_PORT}" ]