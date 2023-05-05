#!/usr/bin/env bash

microk8s kubectl logs $(microk8s kubectl get pod -n kube-system | grep -o "herodotus-scheduler\S*") -n kube-system $1