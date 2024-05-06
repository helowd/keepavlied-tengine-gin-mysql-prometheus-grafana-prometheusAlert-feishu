#!/usr/bin/env python3


import re
import time
import requests
from prometheus_client import start_http_server, Gauge


# Nginx服务器列表
NGINX_SERVERS = [
    {'name': 'loadbalancer_vip', 'type': 'loadbalancer', 'url': 'http://192.168.31.254:80/'},
    {'name': 'web_001', 'type': 'web', 'url': 'http://192.168.31.200:20001/'},
    {'name': 'web_002', 'type': 'web', 'url': 'http://192.168.31.200:20002/'},
    {'name': 'web_003', 'type': 'web', 'url': 'http://192.168.31.200:20003/'}
]

# 资源路径
PATH = {"status": "nginx_status", "reqstat": "nginx_reqstat", "upstream": "upstream_check?format=json"}

# 创建nginx status指标
nginx_active_connections = Gauge('nginx_active_connections', 'Number of active connections in NGINX', labelnames=['server'])
nginx_accepted_connections = Gauge('nginx_accepted_connections', 'Number of accepted connections in NGINX', labelnames=['server'])
nginx_handled_connections = Gauge('nginx_handled_connections', 'Number of handled connections in NGINX', labelnames=['server'])
nginx_total_requests = Gauge('nginx_total_requests', 'Total number of requests handled by NGINX', labelnames=['server'])
nginx_request_time = Gauge('nginx_request_time', 'Average request time in NGINX (in milliseconds)', labelnames=['server'])
nginx_reading_connections = Gauge('nginx_reading_connections', 'Number of connections in NGINX reading request header', labelnames=['server'])
nginx_writing_connections = Gauge('nginx_writing_connections', 'Number of connections in NGINX writing response to client', labelnames=['server'])
nginx_waiting_connections = Gauge('nginx_waiting_connections', 'Number of idle connections in NGINX waiting for request', labelnames=['server'])

# 创建nginx restat指标
nginx_kv = Gauge('nginx_kv', 'kv', labelnames=['server'])
nginx_bytes_in = Gauge('nginx_bytes_in', 'Total bytes received from clients in NGINX', labelnames=['server'])
nginx_bytes_out = Gauge('nginx_bytes_out', 'Total bytes sent to clients in NGINX', labelnames=['server'])
nginx_conn_total = Gauge('nginx_conn_total', 'Total connections handled by NGINX', labelnames=['server'])
nginx_req_total = Gauge('nginx_req_total', 'Total requests handled by NGINX', labelnames=['server'])
nginx_http_2xx = Gauge('nginx_http_2xx', 'Total number of 2xx responses in NGINX', labelnames=['server'])
nginx_http_3xx = Gauge('nginx_http_3xx', 'Total number of 3xx responses in NGINX', labelnames=['server'])
nginx_http_4xx = Gauge('nginx_http_4xx', 'Total number of 4xx responses in NGINX', labelnames=['server'])
nginx_http_5xx = Gauge('nginx_http_5xx', 'Total number of 5xx responses in NGINX', labelnames=['server'])
nginx_http_other_status = Gauge('nginx_http_other_status', 'Total number of other responses in NGINX', labelnames=['server'])
nginx_rt = Gauge('nginx_rt', 'Total request time in NGINX', labelnames=['server'])
nginx_ups_req = Gauge('nginx_ups_req', 'Total requests to upstream in NGINX', labelnames=['server'])
nginx_ups_rt = Gauge('nginx_ups_rt', 'Total upstream request time in NGINX', labelnames=['server'])
nginx_ups_tries = Gauge('nginx_ups_tries', 'Total upstream tries in NGINX', labelnames=['server'])
nginx_http_200 = Gauge('nginx_http_200', 'Total number of 200 responses in NGINX', labelnames=['server'])
nginx_http_206 = Gauge('nginx_http_206', 'Total number of 206 responses in NGINX', labelnames=['server'])
nginx_http_302 = Gauge('nginx_http_302', 'Total number of 302 responses in NGINX', labelnames=['server'])
nginx_http_304 = Gauge('nginx_http_304', 'Total number of 304 responses in NGINX', labelnames=['server'])
nginx_http_403 = Gauge('nginx_http_403', 'Total number of 403 responses in NGINX', labelnames=['server'])
nginx_http_404 = Gauge('nginx_http_404', 'Total number of 404 responses in NGINX', labelnames=['server'])
nginx_http_416 = Gauge('nginx_http_416', 'Total number of 416 responses in NGINX', labelnames=['server'])
nginx_http_499 = Gauge('nginx_http_499', 'Total number of 499 responses in NGINX', labelnames=['server'])
nginx_http_500 = Gauge('nginx_http_500', 'Total number of 500 responses in NGINX', labelnames=['server'])
nginx_http_502 = Gauge('nginx_http_502', 'Total number of 502 responses in NGINX', labelnames=['server'])
nginx_http_503 = Gauge('nginx_http_503', 'Total number of 503 responses in NGINX', labelnames=['server'])
nginx_http_504 = Gauge('nginx_http_504', 'Total number of 504 responses in NGINX', labelnames=['server'])
nginx_http_508 = Gauge('nginx_http_508', 'Total number of 508 responses in NGINX', labelnames=['server'])
nginx_http_other_detail_status = Gauge('nginx_http_other_detail_status', 'Total number of other detailed status responses in NGINX', labelnames=['server'])
nginx_http_ups_4xx = Gauge('nginx_http_ups_4xx', 'Total number of upstream 4xx responses in NGINX', labelnames=['server'])
nginx_http_ups_5xx = Gauge('nginx_http_ups_5xx', 'Total number of upstream 5xx responses in NGINX', labelnames=['server'])

# upstream_check指标
total_servers = Gauge('total_servers', 'Total number of servers', labelnames=['server'])
up_servers = Gauge('up_servers', 'Number of servers up', labelnames=['server'])
down_servers = Gauge('down_servers', 'Number of servers down', labelnames=['server'])
generation = Gauge('generation', 'Generation of servers', labelnames=['server'])
server_up = Gauge('server_up', 'Whether server is up', ['index', 'upstream', 'name', 'type']) 


def update_metrics():
    for server in NGINX_SERVERS:
        response_text = get_nginx_metrics(server, PATH['status'])
        parse_nginx_status(server, response_text)

        if server['type'] == 'loadbalancer':
            response_text = get_nginx_metrics(server, PATH['reqstat'])
            parse_nginx_reqstat(server, response_text)

            response_json = get_nginx_metrics(server, PATH['upstream'])
            parse_upstream_check(server, response_json)
            

def get_nginx_metrics(server, metric):
    try:
        response = requests.get(url=server["url"] + metric)
        if response.status_code == 200:
            return response.json() if metric == PATH['upstream'] else response.text
        else:
            print(f"Failed to fetch NGINX status: {response.status_code}")
    except Exception as e:
        print(f"Failed to fetch NGINX status: {str(e)}")
    return None


def parse_nginx_status(server, nginx_status):
    if not nginx_status:
        return

    active_connections = re.search(r'Active connections:\s+(\d+)', nginx_status)
    if active_connections:
        nginx_active_connections.labels(server=server["name"]).set(int(active_connections.group(1)))

    accepted_handled_requests_time = re.search(r'\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', nginx_status)
    if accepted_handled_requests_time:
        accepted = int(accepted_handled_requests_time.group(1))
        handled = int(accepted_handled_requests_time.group(2))
        requests = int(accepted_handled_requests_time.group(3))
        request_time = int(accepted_handled_requests_time.group(4))
        
        nginx_accepted_connections.labels(server=server["name"]).set(accepted)
        nginx_handled_connections.labels(server=server["name"]).set(handled)
        nginx_total_requests.labels(server=server["name"]).set(requests)
        nginx_request_time.labels(server=server["name"]).set(request_time)

    reading = re.search(r'Reading:\s+(\d+)', nginx_status)
    if reading:
        nginx_reading_connections.labels(server=server["name"]).set(int(reading.group(1)))

    writing = re.search(r'Writing:\s+(\d+)', nginx_status)
    if writing:
        nginx_writing_connections.labels(server=server["name"]).set(int(writing.group(1)))

    waiting = re.search(r'Waiting:\s+(\d+)', nginx_status)
    if waiting:
        nginx_waiting_connections.labels(server=server["name"]).set(int(waiting.group(1)))


def parse_nginx_reqstat(server, nginx_status):
    if not nginx_status:
        return

    lines = nginx_status.strip().split('\n')
    for line in lines:
        kv, bytes_in, bytes_out, conn_total, req_total, http_2xx, http_3xx, http_4xx, http_5xx, http_other_status, rt, ups_req, ups_rt, ups_tries, http_200, http_206, http_302, http_304, http_403, http_404, http_416, http_499, http_500, http_502, http_503, http_504, http_508, http_other_detail_status, http_ups_4xx, http_ups_5xx = line.split(",")
        
        nginx_kv.labels(server=server["name"]).set(1)
        nginx_bytes_in.labels(server=server["name"]).set(bytes_in)
        nginx_bytes_out.labels(server=server["name"]).set(bytes_out)
        nginx_conn_total.labels(server=server["name"]).set(conn_total)
        nginx_req_total.labels(server=server["name"]).set(req_total)
        nginx_http_2xx.labels(server=server["name"]).set(http_2xx)
        nginx_http_3xx.labels(server=server["name"]).set(http_3xx)
        nginx_http_4xx.labels(server=server["name"]).set(http_4xx)
        nginx_http_5xx.labels(server=server["name"]).set(http_5xx)
        nginx_http_other_status.labels(server=server["name"]).set(http_other_status)
        nginx_rt.labels(server=server["name"]).set(rt)
        nginx_ups_req.labels(server=server["name"]).set(ups_req)
        nginx_ups_rt.labels(server=server["name"]).set(ups_rt)
        nginx_ups_tries.labels(server=server["name"]).set(ups_tries)
        nginx_http_200.labels(server=server["name"]).set(http_200)
        nginx_http_206.labels(server=server["name"]).set(http_206)
        nginx_http_302.labels(server=server["name"]).set(http_302)
        nginx_http_304.labels(server=server["name"]).set(http_304)
        nginx_http_403.labels(server=server["name"]).set(http_403)
        nginx_http_404.labels(server=server["name"]).set(http_404)
        nginx_http_416.labels(server=server["name"]).set(http_416)
        nginx_http_499.labels(server=server["name"]).set(http_499)
        nginx_http_500.labels(server=server["name"]).set(http_500)
        nginx_http_502.labels(server=server["name"]).set(http_502)
        nginx_http_503.labels(server=server["name"]).set(http_503)
        nginx_http_504.labels(server=server["name"]).set(http_504)
        nginx_http_508.labels(server=server["name"]).set(http_508)
        nginx_http_other_detail_status.labels(server=server["name"]).set(http_other_detail_status)
        nginx_http_ups_4xx.labels(server=server["name"]).set(http_ups_4xx)
        nginx_http_ups_5xx.labels(server=server["name"]).set(http_ups_5xx)


def parse_upstream_check(host, upstream_check):
    servers_info = upstream_check.get("servers")

    total_servers.labels(server=host['name']).set(servers_info.get('total'))
    up_servers.labels(server=host['name']).set(servers_info.get('up'))
    down_servers.labels(server=host['name']).set(servers_info.get('down'))
    generation.labels(server=host['name']).set(servers_info.get('generation'))

    for server in servers_info.get('server', []):
        server_up.labels(str(server['index']), server['upstream'], server['name'], server['type']).set(1 if server['status'] == 'up' else 0)


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(port=8888, addr='0.0.0.0')

    while True:
        update_metrics()
        time.sleep(10)