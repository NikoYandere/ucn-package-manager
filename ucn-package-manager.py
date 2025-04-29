import os
import sys
import subprocess
import zipfile
import shutil

HOME = os.path.expanduser("~")
REPOS_FILE = os.path.join(HOME, ".local", "share", "ucn-repos", "repos.txt")

def install_ucn(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    url = None
    dependencies = []

    for line in lines:
        if line.startswith('url:'):
            url = line.split('url:')[1].strip()
        if line.startswith('dependencies='):
            dep_line = line.split('dependencies=')[1].strip()
            deps = dep_line.split()
            dependencies.extend(deps)

    if dependencies:
        print("Installing dependencies...")
        install_dependencies(dependencies)

    if url:
        clone_repo(url)

def install_ucr(file_path):
    extract_dir = os.path.join(HOME, os.path.splitext(os.path.basename(file_path))[0])
    print(f"Extracting {file_path}...")
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"Extracted to {extract_dir}")
    except PermissionError:
        print(f"Permission denied while extracting to {extract_dir}")

def install_from_url(url):
    print(f"Cloning repository from {url}...")
    clone_repo(url)

def clone_repo(url):
    target_dir = os.path.join(HOME, url.split('/')[-1].replace('.git', ''))
    subprocess.run(["git", "clone", url, target_dir])

def install_dependencies(dependencies):
    for dep in dependencies:
        if dep.startswith("system:"):
            system_deps = dep.split("system:")[1].split()
            package_manager = detect_package_manager()
            if package_manager:
                subprocess.run([package_manager, "install", "-y"] + system_deps)
        elif dep.startswith("flatpak:"):
            flatpak_deps = dep.split("flatpak:")[1].split()
            subprocess.run(["flatpak", "install", "-y"] + flatpak_deps)
        elif dep.startswith("snap:"):
            snap_deps = dep.split("snap:")[1].split()
            subprocess.run(["snap", "install"] + snap_deps)
        elif dep.startswith("makepkg:"):
            makepkg_deps = dep.split("makepkg:")[1].split()
            for pkg in makepkg_deps:
                subprocess.run(["git", "clone", pkg])
                folder = pkg.split("/")[-1]
                os.chdir(folder)
                subprocess.run(["makepkg", "-si"])

def detect_package_manager():
    managers = ["apt", "dnf", "zypper", "pacman", "xbps-install", "emerge"]
    for manager in managers:
        if shutil.which(manager):
            return manager
    return None

def add_repo(repo_url):
    os.makedirs(os.path.dirname(REPOS_FILE), exist_ok=True)
    with open(REPOS_FILE, 'a') as f:
        f.write(repo_url + "\n")
    print(f"Repository {repo_url} added.")

def remove_repo(repo_name):
    if not os.path.exists(REPOS_FILE):
        print("No repositories added.")
        return
    with open(REPOS_FILE, 'r') as f:
        repos = f.readlines()
    with open(REPOS_FILE, 'w') as f:
        for repo in repos:
            if repo_name not in repo:
                f.write(repo)
    print(f"Repository {repo_name} removed.")

def install_from_repos(package_name):
    if not os.path.exists(REPOS_FILE):
        print("No repositories added.")
        return
    with open(REPOS_FILE, 'r') as f:
        repos = f.readlines()

    for repo in repos:
        repo = repo.strip()
        if package_name in repo:
            install_from_url(repo)
            return

    print(f"Package {package_name} not found in any repository.")

def remove_package(package_name):
    path = os.path.join(HOME, package_name)
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"Package {package_name} removed.")
    else:
        print(f"Package {package_name} not found.")

def update_package(package_name):
    path = os.path.join(HOME, package_name)
    if os.path.exists(path):
        os.chdir(path)
        subprocess.run(["git", "pull"])
        print(f"Package {package_name} updated.")
    else:
        print(f"Package {package_name} not installed.")

def main():
    if len(sys.argv) < 3:
        print("Usage: install <package> | install <url> | install <.ucn/.ucr> | remove <package> | update <package> | add-repo <git-url> | remove-repo <repo-name>")
        return

    command = sys.argv[1]
    target = sys.argv[2]

    if command == "install":
        if target.endswith(".ucn"):
            install_ucn(target)
        elif target.endswith(".ucr"):
            install_ucr(target)
        elif target.startswith("http"):
            install_from_url(target)
        else:
            install_from_repos(target)
    elif command == "remove":
        remove_package(target)
    elif command == "update":
        update_package(target)
    elif command == "add-repo":
        add_repo(target)
    elif command == "remove-repo":
        remove_repo(target)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
