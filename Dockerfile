FROM busybox

LABEL org.opencontainers.image.source=https://github.com/dsmaugy/kubernetes-herodotus

ADD kubernetes_src/_output/dockerized/bin/linux/amd64/kube-scheduler /usr/local/bin/kube-scheduler