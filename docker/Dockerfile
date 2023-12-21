FROM python:3.12-bookworm
VOLUME /minutes
VOLUME /var/db

ADD scripts/ /scripts
RUN /scripts/init.sh

EXPOSE 8001
CMD ["/usr/local/bin/datasette","serve","-h","0.0.0.0", "/var/db/minutes.db"]
