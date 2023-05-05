#!/usr/local/bin/python3

import argparse
import os
import requests
import sys

requests.packages.urllib3.disable_warnings()

OPTION_NODE = "node"
OPTION_POD = "pod"

# TODO: prod implementation would probably take these values from helm chart instead of hard coding
SCHED_ADDR_ENV = "HERODOTUS_SCHEDULER_SERVICE_HOST"
SCHED_PORT_ENV = "HERODOTUS_SCHEDULER_SERVICE_PORT"

NODE_SCORE_PER_POD_PREFIX = "scheduler_normalized_node_score_for_pod"
NODE_SCORE_ATTEMPTS_PREFIX = "scheduler_node_score_attempts"
NODE_SCORE_TOTAL_PREFIX = "scheduler_normalized_node_score_total"
NODE_FILTER_PREFIX = "scheduler_node_filter_status"

# scheduler_node_filter_status{node="microk8s-node-1",plugin="VolumeZone",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 1
# scheduler_normalized_node_score_for_pod{node="microk8s-node-2",plugin="ImageLocality",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 0
# scheduler_normalized_node_score_total{node="darwin-main"} 482
# scheduler_node_score_attempts{node="darwin-main"} 1

# TODO: specific pods require namespace
def cli(options: argparse.Namespace):
    sched_addr = os.environ[SCHED_ADDR_ENV]
    sched_port = os.environ[SCHED_PORT_ENV]
    
    r = requests.get(f"https://{sched_addr}:{sched_port}/metrics", verify=False)
    
    if not r.ok:
        print(f"Error contacting scheduler: {r.text}", file=sys.stderr)
        exit(-1)

    print(r.text)

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="HerodotusEndpoint",
        description="Tool to view data from Herodotus scheduler"
    )

    parser.add_argument('-t', '--type', choices=[OPTION_NODE, OPTION_POD], required=True, help="Choose whether to query data against a pod or a node")
    
    cli(parser.parse_args())