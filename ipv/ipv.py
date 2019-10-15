#!/usr/bin/python

import argparse
import concurrent.futures
from getpass import getpass
import os
import re
import requests
import subprocess
import sys

IPV_DIR = "/usr/local/share/ipv"
SERVER_FILES_DIR = os.path.join(IPV_DIR, "servers")
RANK_FILE = os.path.join(IPV_DIR, "server_ratings.txt")
SERVER_FILES_URL = "https://www.ipvanish.com/software/configs/"
SERVER_FILE_REGEX = r"ipvanish-\w{2}-(.*)-\w{3}-\w\d{2}\.ovpn"


def list_sites():
    regex = f'a href="{SERVER_FILE_REGEX}"'
    site_set = set()

    res = requests.get(SERVER_FILES_URL).content.decode("UTF-8")

    for site in re.findall(regex, res):
        site_set.add(site)

    for site in site_set:
        print(site)


def get_url_from_file(filename):
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

    return sum(times) / ping_count # not using len(times).  Server should be penalized for unreturned ping


def rank():
    try:
        file_list = os.listdir(SERVER_FILES_DIR)
    except FileNotFoundError:
        file_list = []

    if not file_list:
        print("No .ovpn files found.  Please run ipv -d <site>.")
        raise SystemExit(1)

    url_dict = {get_url_from_file(filename): filename for filename in file_list}
    ping_dict = {}

    print(f"Ranking {len(url_dict)} servers.")

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


def env_check():

    crudentials_file = os.path.join(IPV_DIR, "crudentials")

    certificate = "ca.ipvanish.com.crt"
    certificate_file = os.path.join(IPV_DIR, certificate)
    certificate_url = os.path.join(SERVER_FILES_URL, certificate)

    if not os.path.isfile(crudentials_file):
        print("No crudentials saved.")
        username = input("IP Vanish Username: ")
        password = getpass()

        with open(crudentials_file, "w") as crudentials:
            crudentials.write(f"{username}\n{password}\n")

        os.chown(crudentials_file, 0, 0)
        os.chmod(crudentials_file, 0o600)

    if not os.path.isfile(certificate_file):
        cert_data = requests.get(certificate_url).content
        with open(certificate_file, "wb") as cert_file:
            cert_file.write(cert_data)

    if not os.path.isfile(RANK_FILE):
        print("No rank file found.  Please run ipv -rs")
        raise SystemExit(1)


def connect(rank_num):
    env_check()
    with open(RANK_FILE) as infile:
        for line in infile:
            rank, _, filename, _ = line.split('\t')
            if rank == rank_num:
                os.chdir(SERVER_FILES_DIR)
                try:
                    subprocess.run(["openvpn", filename])
                except KeyboardInterrupt:
                    pass
                return
        print(f"Unable to find server with a ranking of {rank_num}", file=sys.stderr)
        raise SystemExit(1)


def download(site):
    regex = f'a href="({SERVER_FILE_REGEX})"'

    if not os.path.isdir(SERVER_FILES_DIR):
        os.makedirs(SERVER_FILES_DIR)

    source = requests.get(SERVER_FILES_URL).content.decode("UTF-8")

    new_server_files = [url for url, city in re.findall(regex, source) if city == site]
    current_server_files = os.listdir(SERVER_FILES_DIR)

    files_to_download = [filename for filename in new_server_files if filename not in current_server_files]

    for filename in files_to_download:
        src_file = os.path.join(SERVER_FILES_URL, filename)
        dst_file = os.path.join(SERVER_FILES_DIR, filename)

        print(f"Downloading from {src_file}")
        data = requests.get(src_file).content.decode("UTF-8")
        # Only .ovpn files should be in server directory
        data = data.replace("ca ", "ca ../")
        data = data.replace("auth-user-pass", "auth-user-pass ../crudentials")
        with open(dst_file, "w") as dest:
            dest.write(data)


def update():
    site_list = set()

    for server_file in os.listdir(SERVER_FILES_DIR):
        match = re.match(SERVER_FILE_REGEX, server_file)
        if match:
            site_list.add(match.groups()[0])

    for site in site_list:
        download(site)


def remove(site):
    for server_file in os.listdir(SERVER_FILES_DIR):
        match = re.match(SERVER_FILE_REGEX, server_file)
        if match and match.groups()[0] == site:
            file_to_remove = os.path.join(SERVER_FILES_DIR, server_file)
            print(f"Removing {file_to_remove}")
            os.remove(file_to_remove)


def init():
    parser = argparse.ArgumentParser(description="Manage or connect to IP Vanish")

    parser.add_argument("--list", "-l", action="store_true", dest="list",
                        help="List all available sites")
    parser.add_argument("--rank-servers", "-r", action="store_true", dest="rank_servers",
                        help="Rank the servers based on ping time")
    parser.add_argument("--server", "-s", action="store", dest="server",
                        help="Connect to server at specified rank.")
    parser.add_argument("--download", "-d", action="store", dest="site",
                        help="Download all files from a particular site")
    parser.add_argument("--update", "-u", action="store_true", dest="update",
                        help="Update server file list")
    parser.add_argument("--remove", "-rm", action="store", dest="remove",
                        help="Delete all files for specified site")
    args = parser.parse_args()

    if args.list:
        list_sites()
        raise SystemExit

    if os.getuid() != 0:
        print("Root access required")
        raise SystemExit(1)

    if args.remove:
        remove(args.remove)

    if args.update:
        update()

    if args.site:  # download
        download(args.site)

    if args.rank_servers:
        rank()

    if args.server:
        connect(args.server)
    elif len(sys.argv) == 1:
        connect("1")


if __name__ == "__main__":
    init()
