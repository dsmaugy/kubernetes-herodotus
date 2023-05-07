from python:3-alpine

LABEL org.opencontainers.image.source=https://github.com/dsmaugy/kubernetes-herodotus

RUN ["pip3", "install", "requests", "termcolor"]

COPY endpoint.py /usr/local/bin/endpoint.py
RUN ["chmod", "+x", "/usr/local/bin/endpoint.py"]

CMD ["python3", "/usr/local/bin/endpoint.py"]