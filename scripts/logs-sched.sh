#!/usr/bin/env bash

kubectl logs $(kubectl get pod -n kube-system | grep -o "herodotus-scheduler\S*") -n kube-system $1