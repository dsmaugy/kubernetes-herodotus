# Herodotus K8s Scheduler

Final project for Spring 2023 CPSC426: Building Distributed Systems.
Taught by Richard Yang and Xiao Shi.

The Herodotus K8s Scheduler is a modified Kubernetes scheduler process that aims to improve transparency and observability in the pod scheduling process. The goal for this project is to reveal the decision-making process behind the Kubernetes scheduler and help cluster operators answer questions such as:
- Why was my pod placed on this node?
- Why does this one node keep getting pods of this specific type?
- Why does my pod balancing look the way it is?
- Any other scheduling-related questions

## Demo Video!

Here is a rather long but informative video showcasing usage of the Herodotus Scheduler:

[gdrive link](https://drive.google.com/file/d/1QQv3CDFR4yaHnIMty8taYCT-4aLbXt0k/view?usp=sharing)

**NOTE**: I use the words "filter" and "plugin" interchangeably a lot. 
To clarify, a scoring filter/plugin is a K8s scheduler check that gives each node a score.
A pure filter plugin is a K8s scheduler step that checks whether or not a node is eligible to have the current node being scheduled. 


## Requirements:
To use this, you need the following:
- Kubernetes cluster with administrator privileges
- `python3` (tested with >=3.8.13 but honestly any relatively modern Python3 should do)

To build the custom scheduler binary, you also need `docker` with `buildx` (see [here](https://github.com/kubernetes/kubernetes/tree/v1.26.4/build#requirements))
This is not required if you just want to test the program, as the built images are hosted on this public Github container registry.

## Installation
1. Run `install.sh` to add the `kubectl herodotus` plugin to PATH. Unless you manually add it to PATH, this moves it to `/usr/local/bin` which requires sudo access.
2. Run `kubectl apply -f deploy/herodotus-scheduler.yml`. This will install all the required service accounts/permissions for the custom scheduler, the custom scheduler itself, the HTTP metric expose endpoint, and any required services to expose the program.

## Building

## Usage

```
usage: HerodotusEndpoint [-h] [-n NAMESPACE] {node,pod} name

Tool to view data from Herodotus scheduler

positional arguments:
  {node,pod}            Choose whether to query data against a pod or a node
  name                  Name of the pod or node to query against

optional arguments:
  -h, --help            show this help message and exit
  -n NAMESPACE, --namespace NAMESPACE
                        Namespace of the pod if querying against pods
```

## Edge Cases:
- Choosing a node when only one option is available
- Choosing a nominated node from preemption
- Specifying specific node name skips scheduler: https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodename
