#!/usr/bin/env python3
import urllib.request
import subprocess
import os

def install_ucn(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    url = None
    dependencies = []
    exec_command = None

    for line in lines:
        if line.startswith('url:'):
            url = line.split('url:')[1].strip()
        elif line.startswith('dependencies='):
            dep_line = line.split('dependencies=')[1].strip()
            dependencies.extend(dep_line.split())
        elif line.startswith('exec='):
            exec_command = line.split('exec=')[1].strip()

    if dependencies:
        install_dependencies(dependencies)

    if url:
        clone_repo(url)

    if exec_command:
        try:
            subprocess.run(exec_command, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Error while executing {exec_command}: {e}")
        except FileNotFoundError:
            print(f"Executable {exec_command} not found. Please ensure it is in your PATH.")

def install_from_repos(package_name):
    if not os.path.exists(REPOS_FILE):
        print("No repositories added.")
        return

    with open(REPOS_FILE, 'r') as f:
        repos = f.readlines()

    for repo in repos:
        repo = repo.strip().rstrip('/')
        ucn_url = f"{repo}/{package_name}.ucn"
        try:
            print(f"Trying to download {ucn_url}...")
            local_path = os.path.join("/tmp", f"{package_name}.ucn")
            urllib.request.urlretrieve(ucn_url, local_path)
            print(f"Downloaded {package_name}.ucn")
            install_ucn(local_path)
            os.remove(local_path)
            return
        except Exception as e:
            print(f"Failed to download from {repo}: {e}")

    print(f"Package {package_name} not found in any repository.")
