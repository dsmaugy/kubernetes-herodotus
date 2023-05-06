#!/usr/bin/env bash

SCRIPT_DIR=$( dirname -- "$0")

$SCRIPT_DIR/../kubernetes_src/build/run.sh make kube-scheduler

docker build . --tag ghcr.io/dsmaugy/kubernetes-herodotus/herodotus-scheduler:latest
docker push  ghcr.io/dsmaugy/kubernetes-herodotus/herodotus-scheduler:latest

kubectl rollout restart deploy herodotus-scheduler -n kube-system