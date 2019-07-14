FROM continuumio/anaconda3:latest

RUN groupadd -g 999 appuser && \
    useradd -m -r -u 999 -g appuser appuser

ADD . /app
WORKDIR /app

RUN python3 -m ensurepip

# Prevent nginx from starting automatically
RUN ln -s /dev/null /etc/systemd/system/nginx.service

RUN apt-get update -y
RUN apt-get install -y apt-utils redis-server supervisor nginx libpq-dev gcc g++ make build-essential

RUN echo never > /sys/kernel/mm/transparent_hugepage/enabled

RUN curl -sL https://deb.nodesource.com/setup_9.x | bash
RUN apt-get install -yqq nodejs
RUN apt-get clean -y

# RUN python3 -m pip install celery==4.2.2 # Because Celery 4.3 is broken
RUN pip install -r server/localrequirements.txt
RUN python3 setup.py develop

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm -f /etc/nginx/conf.d/*
RUN rm -f /etc/nginx/sites-enabled/*
COPY build/nginx.conf /etc/nginx/conf.d/nginx.conf

RUN rm -rf client/node_modules
RUN npm install -g bower
RUN npm install -g gulp

COPY server/config.example.py server/config.py
RUN ./bin/build_client.sh

EXPOSE 80 443

RUN chown -R appuser:appuser .
CMD supervisord
