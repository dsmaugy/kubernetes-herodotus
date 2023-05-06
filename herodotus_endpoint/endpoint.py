#!/usr/local/bin/python3

from termcolor import cprint, colored
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Union

import argparse
import os
import requests
import sys
import re
import json
import logging

requests.packages.urllib3.disable_warnings() # type: ignore

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
NODE_SCORE_PER_POD_RE = r''

NO_NODE_FOUND_ERROR = 0
REGEX_ERROR_ERROR = 1

# scheduler_node_filter_status{node="microk8s-node-1",plugin="VolumeZone",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 1
# scheduler_normalized_node_score_for_pod{node="microk8s-node-2",plugin="ImageLocality",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 0
# scheduler_normalized_node_score_total{node="darwin-main"} 482
# scheduler_node_score_attempts{node="darwin-main"} 1
# scheduler_node_filter_pass{node="darwin-main",plugin="VolumeBinding"} 1
# scheduler_node_filter_attempts{node="microk8s-node-2",plugin="GCEPDLimits"} 1

# TODO: specific pods require namespace
# cprint(f"{options.name}:\n", attrs=["underline"])
# cprint("\tNode Scores:", color="cyan", attrs=["bold"])
# print(f"\t\t{colored('Total Accumulated Score', color='green')}: {node_score_total}")
# print(f"\t\t{colored('Total Score Attempts', color='green')}: {node_score_attempts}\n")
# cprint("\tNode Filter Pass Rate:", color="cyan", attrs=["bold"])
# for filterPlugin, val in node_filter_attempts.items:
#     print(f"\t\t\t\t{colored(f'{filterPlugin}', color='green')}: {val}")
            

class HerodotusEndpoint(BaseHTTPRequestHandler):

    def _send_header(self, code: int, type="application/json"):
        self.send_response(code)
        self.send_header("Content-type", type)
        self.end_headers()

    def _send_text(self, text: str):
        self.wfile.write(bytes(text, encoding="utf-8"))

    def _handle_node_request(self, request: requests.Response, node_name: str) -> Tuple[Union[dict, int], Union[str, None]]:
        node_filter_pass = node_filter_attempts = dict()
        node_score_total = node_score_attempts = 0

        logging.info(f"Processing NODE request for node: {node_name}")
        found_node = False
        for line in request.text.splitlines():
            if line.startswith(NODE_FILTER_PASS_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_FILTER_PASS_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_FILTER_PASS_RE}"

                node_filter_pass[search.group(1)] = int(search.group(2))
            elif line.startswith(NODE_FILTER_ATTEMPTS_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_FILTER_ATTEMPTS_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_FILTER_ATTEMPTS_RE}"
                
                node_filter_attempts[search.group(1)] = int(search.group(2))
            elif line.startswith(NODE_SCORE_ATTEMPTS_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_SCORE_ATTEMPTS_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_SCORE_ATTEMPTS_RE}"
                
                node_score_attempts = int(search.group(1))
            elif line.startswith(NODE_SCORE_TOTAL_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_SCORE_TOTAL_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_SCORE_TOTAL_RE}"
                
                # arbitarily use node total score to mark whether a node has been found but any should work
                found_node = True 
                node_score_total = int(search.group(1))

        if not found_node:
            return NO_NODE_FOUND_ERROR, f"No node found with name {node_name}"

        return {
            'node_score_total': node_score_total,
            'node_score_attempts': node_score_attempts,
            'node_filter_pass': node_filter_pass,
            'node_filter_attempts': node_filter_attempts,
        }, None
    
    def _handle_pod_request(self, request: requests.Response, pod_name: str, namespace: str) -> Tuple[Union[dict, int], Union[str, None]]:
        for line in request.text.splitlines():
            if line.startswith(NODE_SCORE_PER_POD_PREFIX):
                pass
            elif line.startswith(NODE_FILTER_STATUS_PREFIX):
                pass

    def do_GET(self):
        sched_addr = os.environ[SCHED_ADDR_ENV]
        sched_port = os.environ[SCHED_PORT_ENV]

        parse = urlparse(self.path)
        query_comp = parse_qs(parse.query)
      
        if 'name' not in query_comp.keys():
            self._send_header(400)
            self._send_text("Empty name in query")
            return
        
        r = requests.get(f"https://{sched_addr}:{sched_port}/metrics", verify=False)

        if not r.ok:
            self._send_header(500, "text/plain")
            self._send_text(f"Error contacting scheduler: {r.text}")
            return

        if parse.path.lower() == "/node":
            out, err = self._handle_node_request(r, query_comp['name'][0])
            if err == None:
                self._send_header(200)
                self._send_text(json.dumps(out))
            else:
                if out == NO_NODE_FOUND_ERROR:
                    self._send_header(404)
                else:
                    self._send_header(400, type="text/plain")
                self._send_text(err)
        elif parse.path.lower() == "/pod":
            pass
        else:
            self._send_header(400)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(
    #     prog="HerodotusEndpoint",
    #     description="Tool to view data from Herodotus scheduler"
    # )

    # parser.add_argument('type', choices=[OPTION_NODE, OPTION_POD], help="Choose whether to query data against a pod or a node")
    # parser.add_argument('name', help="Name of the pod or node to query against")
    # parser.add_argument('-n', '--namespace', required=False, default="default", help="Namespace of the pod if querying against pods")
    
    # cli(parser.parse_args())

    # TODO: kubectl logs --follow makes it so it's impossible to quit
    addr = ('', 8000)
    httpd = HTTPServer(addr, HerodotusEndpoint)
    httpd.serve_forever()

