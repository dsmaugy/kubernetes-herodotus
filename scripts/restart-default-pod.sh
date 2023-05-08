#!/usr/bin/env bash

SCRIPT_DIR=$( dirname -- "$0")

kubectl delete pod test-pod-1

kubectl apply -f $SCRIPT_DIR/../deploy/test/deploy-default-pod.yml