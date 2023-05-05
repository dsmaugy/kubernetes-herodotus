#!/usr/local/bin/python3

import argparse
import os
import requests

OPTION_NODE = "node"
OPTION_POD = "pod"

# TODO: prod implementation would probably take these values from helm chart instead of hard coding
SCHED_ADDR_ENV = "HERODOTUS_SCHEDULER_SERVICE_HOST"
SCHED_PORT_ENV = "HERODOTUS_SCHEDULER_SERVICE_PORT"

SCHED_ADDR = os.environ[SCHED_ADDR_ENV]
SCHED_PORT = os.environ[SCHED_PORT_ENV]

# TODO: specific pods require namespace
def cli(options: argparse.Namespace):
    r = requests.get(f"https://{SCHED_ADDR}:{SCHED_PORT}/metrics", verify=False)
    print(r.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="HerodotusEndpoint",
        description="Tool to view data from Herodotus scheduler"
    )

    parser.add_argument('-t', '--type', choices=[OPTION_NODE, OPTION_POD], required=True, help="Choose whether to query data against a pod or a node")
    
    cli(parser.parse_args())