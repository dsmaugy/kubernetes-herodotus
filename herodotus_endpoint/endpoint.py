#!/usr/local/bin/python3

from termcolor import cprint, colored

import argparse
import os
import requests
import sys
import re


requests.packages.urllib3.disable_warnings()

OPTION_NODE = "node"
OPTION_POD = "pod"

# TODO: prod implementation would probably take these values from helm chart instead of hard coding
SCHED_ADDR_ENV = "HERODOTUS_SCHEDULER_SERVICE_HOST"
SCHED_PORT_ENV = "HERODOTUS_SCHEDULER_SERVICE_PORT"

NODE_SCORE_PER_POD_PREFIX = "scheduler_normalized_node_score_for_pod"
NODE_SCORE_ATTEMPTS_PREFIX = 'scheduler_node_score_attempts{{node="{node_name}"'
NODE_SCORE_TOTAL_PREFIX = 'scheduler_normalized_node_score_total{{node="{node_name}"'
NODE_FILTER_STATUS_PREFIX = "scheduler_node_filter_status"
NODE_FILTER_PASS_PREFIX = 'scheduler_node_filter_pass{{node="{node_name}"'
NODE_FILTER_ATTEMPTS_PREFIX = 'scheduler_node_filter_attempts{{node="{node_name}"'

NODE_FILTER_PASS_RE = r'plugin="([^"]+)"} (\d+)'
NODE_FILTER_ATTEMPTS_RE = r'plugin="([^"]+)"} (\d+)'
NODE_SCORE_ATTEMPTS_RE = r'node="[^"]+"} (\d+)'
NODE_SCORE_TOTAL_RE = r'node="[^"]+"} (\d+)'

# scheduler_node_filter_status{node="microk8s-node-1",plugin="VolumeZone",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 1
# scheduler_normalized_node_score_for_pod{node="microk8s-node-2",plugin="ImageLocality",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 0
# scheduler_normalized_node_score_total{node="darwin-main"} 482
# scheduler_node_score_attempts{node="darwin-main"} 1
# scheduler_node_filter_pass{node="darwin-main",plugin="VolumeBinding"} 1
# scheduler_node_filter_attempts{node="microk8s-node-2",plugin="GCEPDLimits"} 1

def handle_regex_error(line: str, pattern: str):
    print(f"Error matching {line} with pattern {pattern}", file=sys.stderr)
    exit(-1)

# TODO: specific pods require namespace
def cli(options: argparse.Namespace):
    sched_addr = os.environ[SCHED_ADDR_ENV]
    sched_port = os.environ[SCHED_PORT_ENV]
    
    r = requests.get(f"https://{sched_addr}:{sched_port}/metrics", verify=False)
    
    if not r.ok:
        print(f"Error contacting scheduler: {r.text}", file=sys.stderr)
        exit(-1)

    if options.type == OPTION_NODE:
        node_filter_pass = node_filter_attempts = dict()
        node_score_total = node_score_attempts = 0
        for line in r.text.splitlines():
            if line.startswith(NODE_FILTER_PASS_PREFIX.format(node_name=options.name)):
                search = re.search(NODE_FILTER_PASS_RE, line)
                if search is None:
                    handle_regex_error(line, NODE_FILTER_PASS_RE)

                node_filter_pass[search.group(1)] = int(search.group(2))
            elif line.startswith(NODE_FILTER_ATTEMPTS_PREFIX.format(node_name=options.name)):
                search = re.search(NODE_FILTER_ATTEMPTS_RE, line)
                if search is None:
                    handle_regex_error(line, NODE_FILTER_ATTEMPTS_RE)
                
                node_filter_attempts[search.group(1)] = int(search.group(2))
            elif line.startswith(NODE_SCORE_ATTEMPTS_PREFIX.format(node_name=options.name)):
                search = re.search(NODE_SCORE_ATTEMPTS_RE, line)
                if search is None:
                    handle_regex_error(line, NODE_SCORE_ATTEMPTS_RE)

                node_score_attempts = int(search.group(1))
            elif line.startswith(NODE_SCORE_TOTAL_PREFIX.format(node_name=options.name)):
                search = re.search(NODE_SCORE_TOTAL_RE, line)
                if search is None:
                    handle_regex_error(line, NODE_SCORE_TOTAL_RE)

                node_score_total = int(search.group(1))

        cprint(f"{options.name}:\n", attrs=["underline"])
        cprint("\tNode Scores:", color="cyan", attrs=["bold"])
        print(f"\t\t{colored('Total Accumulated Score', color='green')}: {node_score_total}")
        print(f"\t\t{colored('Total Score Attempts', color='green')}: {node_score_attempts}\n")
        cprint("\tNode Filter Pass Rate:", color="cyan", attrs=["bold"])
        # for filterPlugin, val in node_filter_attempts.items:
        #     print(f"\t\t\t\t{colored(f'{filterPlugin}', color='green')}: {val}")
            

    elif options.type == OPTION_POD:
        pass

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="HerodotusEndpoint",
        description="Tool to view data from Herodotus scheduler"
    )

    parser.add_argument('type', choices=[OPTION_NODE, OPTION_POD], help="Choose whether to query data against a pod or a node")
    parser.add_argument('name', help="Name of the pod or node to query against")
    parser.add_argument('-n', '--namespace', required=False, default="default", help="Namespace of the pod if querying against pods")
    
    cli(parser.parse_args())