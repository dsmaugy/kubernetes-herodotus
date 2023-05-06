#!/usr/bin/env bash

SCRIPT_DIR=$( dirname -- "$0")

docker build $SCRIPT_DIR/../herodotus_endpoint --tag ghcr.io/dsmaugy/kubernetes-herodotus/herodotus-endpoint:latest
docker push ghcr.io/dsmaugy/kubernetes-herodotus/herodotus-endpoint:latest

kubectl rollout restart deploy herodotus-endpoint -n kube-system