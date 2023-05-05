#!/usr/bin/env bash

SCRIPT_DIR=$( dirname -- "$0")

microk8s kubectl delete pod annotation-default-scheduler

microk8s kubectl apply -f $SCRIPT_DIR/../deploy/deploy-default-pod.yml