#!/usr/bin/python

import argparse
import concurrent.futures
import os
import re
import subprocess
import sys

IPV_DIR = "/usr/local/share/ipv"
SERVER_FILES_DIR = os.path.join(IPV_DIR, "servers")
RANK_FILE = os.path.join(IPV_DIR, "server_ratings.txt")

#TODO Pull all servers from website

def get_url(filename):
    filename = os.path.join(SERVER_FILES_DIR, filename)
    regex = "remote (.*) 443"
    with open(filename) as currfile:
        match = re.search(regex, currfile.read())
        return match.groups()[0]

def get_avg_ping(url, ping_count=5):
    regex = "time=(.*) ms"
    ping_result = subprocess.run(["ping", "-i 0.2", f"-c {ping_count}", url], capture_output=True, text=True)
    output = ping_result.stdout
    times = [float(time) for time in re.findall(regex, output)]

    return sum(times) / ping_count # not using sum(times).  Server should be penalized for unreturned ping

def rank():
    
    file_list = os.listdir(SERVER_FILES_DIR)
    url_dict = {get_url(filename): filename for filename in file_list}
    ping_dict = {}
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = {executor.submit(get_avg_ping, url): url for url in url_dict.keys()}
        for f in concurrent.futures.as_completed(results):
            ping_dict[results[f]] = f.result()

    ranked_list = sorted(ping_dict.items(), key=lambda item: item[1])
    
    with open(RANK_FILE, "w") as outfile:
        for rank, item in enumerate(ranked_list, 1):
            server, time = item
            filename = url_dict[server]
            outfile.write(f"{rank}\t{server}\t{filename}\t{time}\n")

def connect(rank_num):
    with open(RANK_FILE) as infile:
        for line in infile:
            rank, _, filename, _ = line.split('\t')
            if rank == rank_num:
                os.chdir(SERVER_FILES_DIR)
                os.system(f"openvpn {filename}")
                return
        print(f"Unable to find server with a ranking of {rank_num}", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage or connect to IP Vanish")

    parser.add_argument("--rank-servers", "-rs", action="store_true", dest="rank_servers", help="Rank the servers based on ping time")
    parser.add_argument("--server", "-s", action="store", dest="server", default="1", help="Connect to server at specified rank.")
    args = parser.parse_args()

    if args.rank_servers:
        rank()
        exit(0)
    connect(args.server)
