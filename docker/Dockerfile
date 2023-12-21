FROM ubuntu
ADD scripts/ /scripts
RUN /scripts/init.sh
VOLUME /minutes
VOLUME /var/db
EXPOSE 8001
CMD ["/usr/local/bin/datasette","serve","-h","0.0.0.0", "/var/db/minutes.db"]
