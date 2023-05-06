from python:3-alpine

LABEL org.opencontainers.image.source=https://github.com/dsmaugy/kubernetes-herodotus

RUN ["pip3", "install", "requests", "termcolor"]

COPY endpoint.py /usr/local/bin/endpoint
RUN ["chmod", "+x", "/usr/local/bin/endpoint"]

CMD ["endpoint"]