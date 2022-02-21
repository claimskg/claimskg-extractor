FROM redis
LABEL maintainer="Sascha Schueller <sascha.schueller@gesis.org>"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev git

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY . /app
CMD [ "redis-server" ]
