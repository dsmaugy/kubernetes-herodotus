#!/usr/bin/env bash

SCRIPT_DIR=$( dirname -- "$0")

docker build $SCRIPT_DIR/../herodotus_endpoint --tag ghcr.io/dsmaugy/kubernetes-herodotus/herodotus-endpoint:latest
docker push ghcr.io/dsmaugy/kubernetes-herodotus/herodotus-endpoint:latest

microk8s kubectl delete pod herodotus-endpoint -n kube-system
microk8s kubectl apply -f $SCRIPT_DIR/../deploy/scheduler-stats-endpoint.yml