#!/usr/bin/env bash

SCRIPT_DIR=$( dirname -- "$0")

kubectl delete pod annotation-default-scheduler

kubectl apply -f $SCRIPT_DIR/../deploy/deploy-default-pod.yml