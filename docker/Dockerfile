FROM python:3.12
ADD . /cobb-tracker
RUN cd /cobb-tracker; pip install .; pip install datasette;
CMD ["cobb-tracker"]
VOLUME /minutes
