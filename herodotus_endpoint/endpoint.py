#!/usr/bin/python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Union
from collections import defaultdict

import os
import requests
import re
import json
import logging

requests.packages.urllib3.disable_warnings() # type: ignore

# TODO: prod implementation would probably take these values from helm chart instead of hard coding
SCHED_ADDR_ENV = "HERODOTUS_SCHEDULER_SERVICE_HOST"
SCHED_PORT_ENV = "HERODOTUS_SCHEDULER_SERVICE_PORT"

NODE_SCORE_PER_POD_PREFIX = 'scheduler_normalized_node_score_for_pod'
NODE_SCORE_PER_PLUGIN_TOTAL_PREFIX = 'scheduler_node_score_by_plugin_total{{node="{node_name}"'
NODE_SCORE_ATTEMPTS_PREFIX = 'scheduler_node_score_attempts{{node="{node_name}"'
NODE_SCORE_TOTAL_PREFIX = 'scheduler_normalized_node_score_total{{node="{node_name}"'
NODE_FILTER_STATUS_PREFIX = "scheduler_node_filter_status"
NODE_FILTER_PASS_PREFIX = 'scheduler_node_filter_pass{{node="{node_name}"'
NODE_FILTER_ATTEMPTS_PREFIX = 'scheduler_node_filter_attempts{{node="{node_name}"'
NODE_ELIGIBLE_PREFIX = 'scheduler_node_eligible_num{{node="{node_name}"'
NODE_ELIGIBLE_CHECK_PREFIX = 'scheduler_node_eligible_check_num{{node="{node_name}"'


NODE_FILTER_PASS_RE = r'plugin="([^"]+)"} (\d+)'
NODE_FILTER_ATTEMPTS_RE = r'plugin="([^"]+)"} (\d+)'
NODE_SCORE_ATTEMPTS_RE = r'node="[^"]+"} (\d+)'
NODE_SCORE_TOTAL_RE = r'node="[^"]+"} (\d+)'
NODE_SCORE_PER_POD_RE = r'node="([^"]+)",plugin="([^"]+)",' + 'pod="kubernetes.io/herodotus-scheduler/{namespace}/{pod_name}"}}' + r' (\d+)'
NODE_FILTER_STATUS_PER_POD_RE = r'node="([^"]+)",plugin="([^"]+)",' + 'pod="kubernetes.io/herodotus-scheduler/{namespace}/{pod_name}"}}' + r' (\d+)'
NODE_SCORE_PER_PLUGIN_TOTAL_RE = r'node="[^"]+",plugin="([^"]+)"} (\d+)'
NODE_ELIGIBLE_RE = r'node="[^"]+"} (\d+)'
NODE_ELIGIBLE_CHECK_RE = r'node="[^"]+"} (\d+)'

NOT_FOUND_ERROR = 0
REGEX_ERROR_ERROR = 1

# scheduler_node_filter_status{node="microk8s-node-1",plugin="VolumeZone",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 1
# scheduler_normalized_node_score_for_pod{node="microk8s-node-2",plugin="ImageLocality",pod="kubernetes.io/herodotus-scheduler/default/annotation-default-scheduler"} 0
# scheduler_normalized_node_score_total{node="darwin-main"} 482
# scheduler_node_score_attempts{node="darwin-main"} 1
# scheduler_node_filter_pass{node="darwin-main",plugin="VolumeBinding"} 1
# scheduler_node_filter_attempts{node="microk8s-node-2",plugin="GCEPDLimits"} 1
# node_score_by_plugin_total{node=, plugin=} XX


            

class HerodotusEndpoint(BaseHTTPRequestHandler):

    def _send_header(self, code: int, type="application/json"):
        self.send_response(code)
        self.send_header("Content-type", type)
        self.end_headers()

    def _send_text(self, text: str):
        self.wfile.write(bytes(text, encoding="utf-8"))

    def _get_pod_key(self, pod: str, namespace: str):
        return f"kubernetes.io/herodotus-scheduler/{namespace}/{pod}"

    def _handle_node_request(self, request: requests.Response, node_name: str) -> Tuple[Union[dict, int], Union[str, None]]:
        node_filter_pass = dict()
        node_filter_attempts = dict()
        node_score_plugin_totals = dict()
        node_score_total = node_score_attempts = node_eligible_num = node_eligible_check_num = -1  # sentinel debug value

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
            elif line.startswith(NODE_SCORE_PER_PLUGIN_TOTAL_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_SCORE_PER_PLUGIN_TOTAL_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_SCORE_PER_PLUGIN_TOTAL_RE}"
                
                node_score_plugin_totals[search.group(1)] = search.group(2)
            elif line.startswith(NODE_ELIGIBLE_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_ELIGIBLE_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_ELIGIBLE_RE}"
                
                node_eligible_num = int(search.group(1))
            elif line.startswith(NODE_ELIGIBLE_CHECK_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_ELIGIBLE_CHECK_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_ELIGIBLE_CHECK_RE}"
                
                node_eligible_check_num = int(search.group(1))
            elif line.startswith(NODE_SCORE_TOTAL_PREFIX.format(node_name=node_name)):
                search = re.search(NODE_SCORE_TOTAL_RE, line)
                if search is None:
                    return REGEX_ERROR_ERROR, f"Error matching {line} with pattern {NODE_SCORE_TOTAL_RE}"
                
                # arbitarily use node total score to mark whether a node has been found but any should work
                found_node = True 
                node_score_total = int(search.group(1))

            # TODO: handle node_score_by_plugin_total

        if not found_node:
            return NOT_FOUND_ERROR, f"No node found with name {node_name}"

        return {
            'node_score_total': node_score_total,
            'node_score_attempts': node_score_attempts,
            'node_score_plugin_total': node_score_plugin_totals,
            'node_filter_pass': node_filter_pass,
            'node_filter_attempts': node_filter_attempts,
            'node_eligible_num': node_eligible_num,
            'node_eligible_check_num': node_eligible_check_num,
        }, None
    
    def _handle_pod_request(self, request: requests.Response, pod_name: str, namespace: str) -> Tuple[Union[dict, int], Union[str, None]]:
        pod_filter_scores = defaultdict(lambda: defaultdict(dict))
        pod_filter_status = defaultdict(lambda: defaultdict(dict))
        found_pod_scores = found_pod_status = skipped_scoring = False
        for line in request.text.splitlines():
            if line.startswith(NODE_SCORE_PER_POD_PREFIX):
                print(line)
                search = re.search(NODE_SCORE_PER_POD_RE.format(namespace=namespace, pod_name=pod_name), line)
                if search:
                    found_pod_scores = True 

                    pod_filter_scores[pod_name][search.group(1)][search.group(2)] = float(search.group(3))
            elif line.startswith(NODE_FILTER_STATUS_PREFIX):
                print(line)
                search = re.search(NODE_FILTER_STATUS_PER_POD_RE.format(namespace=namespace, pod_name=pod_name), line)
                if search:
                    pod_filter_status[pod_name][search.group(1)][search.group(2)] = int(search.group(3))
                    found_pod_status = True
        
        if not found_pod_scores and not found_pod_status:
            return NOT_FOUND_ERROR, f"No pod found with name {pod_name} under namespace {namespace}"
        elif not found_pod_scores and found_pod_status:
            skipped_scoring = True
        
        return {
            "filter_scores": pod_filter_scores,
            "filter_status": pod_filter_status,
            "skipped_scoring": skipped_scoring,
        }, None
    
    def do_GET(self):
        sched_addr = os.environ[SCHED_ADDR_ENV]
        sched_port = os.environ[SCHED_PORT_ENV]

        parse = urlparse(self.path)
        query_comp = parse_qs(parse.query)
      
        if 'name' not in query_comp.keys():
            self.send_error(400, "Empty name in query")
            return
        
        try:
            r = requests.get(f"https://{sched_addr}:{sched_port}/metrics", verify=False)
        except Exception:
            r = None

        if r is None or not r.ok:
            self._send_header(500, "text/plain")
            self._send_text(f"Error contacting scheduler")
            return

        if parse.path.lower() == "/node":
            out, err = self._handle_node_request(r, query_comp['name'][0])
            if err == None:
                self._send_header(200)
                self._send_text(json.dumps(out))
            else:
                if out == NOT_FOUND_ERROR:
                    self.send_error(404, err)
                else:
                    self.send_error(400, err)
            
        elif parse.path.lower() == "/pod":
            if 'namespace' not in query_comp.keys():
                self._send_header(400, type="text/plain")
                self._send_text("No namespace given for query")
                return
            
            out, err = self._handle_pod_request(r, query_comp['name'][0], query_comp['namespace'][0])
            if err == None:
                self._send_header(200)
                self._send_text(json.dumps(out))
            else:
                if out == NOT_FOUND_ERROR:
                    self.send_error(404, err)
                else:
                    self.send_error(400, err)
        else:
            self.send_error(404, "Bad Text")


if __name__ == "__main__":
    # TODO: kubectl logs --follow makes it so it's impossible to quit
    addr = ('', 8000)
    httpd = HTTPServer(addr, HerodotusEndpoint)
    httpd.serve_forever()

