FROM selenium/standalone-chrome

RUN sudo apt-get update
RUN sudo apt-get install python3 python3-pip gunicorn3 -y

COPY requirements.txt requirements.txt

RUN pip3 install -r ./requirements.txt

COPY . .

RUN ["sudo", "chmod", "+x", "entrypoint.sh"]

ENV BASE_URL=https://thepiratebay.org/
ENV HOME_BASE=http://172.25.0.2:9091/transmission/rpc

ENTRYPOINT ["./entrypoint.sh", "8000" ]