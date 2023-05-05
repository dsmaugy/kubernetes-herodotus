from python:3-alpine

LABEL org.opencontainers.image.source=https://github.com/dsmaugy/kubernetes-herodotus

COPY endpoint.py /usr/local/bin/endpoint

RUN ["chmod", "+x", "/usr/local/bin/endpoint"]
RUN ["pip3", "install", "requests", "termcolor"]

CMD ["tail", "-f", "/dev/null"]