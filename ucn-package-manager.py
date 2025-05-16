#!/usr/bin/env python3
import os
import sys
import subprocess
import zipfile
import shutil
import urllib.request

HOME = os.path.expanduser("~")
REPOS_FILE = os.path.join(HOME, ".local", "share", "ucn-repos", "repos.txt")
PKG_BASE_DIR = os.path.join(HOME, ".ucndata", "packages")
PM_COMMANDS = {
    "apt":    {"update": ["apt", "update"],     "install": ["apt", "install", "-y"]},
    "dnf":    {"update": ["dnf", "makecache"],  "install": ["dnf", "install", "-y"]},
    "zypper": {"update": ["zypper", "refresh"],  "install": ["zypper", "install", "-y"]},
    "pacman": {"update": ["pacman", "-Sy"],      "install": ["pacman", "-S", "--noconfirm"]},
    "xbps-install": {"update": ["xbps-install", "-Sy"], "install": ["xbps-install", "-S", "-y"]},
    "emerge": {"update": None,                     "install": ["emerge"]}
}

def run_sudo(cmd_list):
    if os.geteuid() != 0:
        cmd_list.insert(0, "sudo")
    subprocess.run(cmd_list, check=True)

def detect_package_manager():
    for pm in PM_COMMANDS:
        if shutil.which(pm):
            return pm
    return None

def parse_manifest(manifest_text):
    meta = {}
    deps = {}
    lines = manifest_text.splitlines()
    current = None
    acc = []
    last_key = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        if ':' in line and current is None:
            k, v = line.split(':', 1)
            meta[k.strip().lower()] = v.strip()
        elif line.lower() == 'dependencies':
            current = 'deps'
        elif current == 'deps':
            if line.startswith('(') and line.endswith(')'):
                if acc and last_key:
                    deps[last_key] = acc
                last_key = line[1:-1].lower()
                acc = []
            else:
                if line:
                    acc.extend(line.split())
    if current == 'deps' and acc and last_key:
        deps[last_key] = acc
    meta['dependencies'] = deps
    return meta

def install_dependencies(deps):
    pm = detect_package_manager()
    for d, pkgs in deps.items():
        if d == 'winetricks':
            for pkg in pkgs:
                run_sudo(["winetricks", pkg])
        elif d == 'flatpak':
            run_sudo(["flatpak", "install", "-y"] + pkgs)
        elif d == 'snap':
            run_sudo(["snap", "install"] + pkgs)
        elif d == 'makepkg':
            cwd = os.getcwd()
            for repo in pkgs:
                run_sudo(["git", "clone", repo])
                folder = os.path.basename(repo)
                os.chdir(folder)
                run_sudo(["makepkg", "-si"])
                os.chdir(cwd)
        else:
            if d == pm:
                cmds = PM_COMMANDS[pm]
                if cmds.get('update'):
                    run_sudo(cmds['update'])
                run_sudo(cmds['install'] + pkgs)

def extract_ucn_package(file_path, package_name):
    target = os.path.join(PKG_BASE_DIR, package_name)
    os.makedirs(target, exist_ok=True)
    with zipfile.ZipFile(file_path, 'r') as z:
        root = None
        for f in z.namelist():
            if '/' in f:
                root = f.split('/', 1)[0]
                break
        for member in z.namelist():
            if root and member.startswith(root + '/'):
                rel = member[len(root)+1:]
            else:
                rel = member
            if not rel:
                continue
            path = os.path.join(target, rel)
            if member.endswith('/'):
                os.makedirs(path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with z.open(member) as src, open(path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)

def install_ucn(file_path):
    with zipfile.ZipFile(file_path, 'r') as z:
        manifest = None
        for f in z.namelist():
            if f.endswith('-manifest'):
                manifest = f
                break
        if not manifest:
            print("Manifest not found")
            return
        text = z.read(manifest).decode('utf-8')
    meta = parse_manifest(text)
    name = meta.get('name')
    if not name:
        print("Name missing")
        return
    deps = meta.get('dependencies', {})
    if deps:
        install_dependencies(deps)
    extract_ucn_package(file_path, name)
    cmd = meta.get('exec')
    if cmd:
        subprocess.run(cmd, shell=True, check=True, cwd=os.path.join(PKG_BASE_DIR, name))

def run_ucn(pkg_name):
    if pkg_name.endswith('.ucn'):
        pkg_name = pkg_name[:-4]
    pkg_dir = os.path.join(PKG_BASE_DIR, pkg_name)
    if not os.path.isdir(pkg_dir):
        print(f"Package {pkg_name} not installed")
        return
    manifest_path = None
    for root, _, files in os.walk(pkg_dir):
        for f in files:
            if f.endswith('-manifest'):
                manifest_path = os.path.join(root, f)
                break
        if manifest_path:
            break
    if not manifest_path:
        print("Manifest not found")
        return
    with open(manifest_path) as mf:
        text = mf.read()
    meta = parse_manifest(text)
    cmd = meta.get('exec')
    if not cmd:
        print("No exec command in manifest")
        return
    subprocess.run(cmd, shell=True, check=True, cwd=pkg_dir)

def add_repo(url):
    os.makedirs(os.path.dirname(REPOS_FILE), exist_ok=True)
    with open(REPOS_FILE, 'a') as f:
        f.write(url.rstrip('/') + "\n")

def remove_repo(name):
    if not os.path.exists(REPOS_FILE):
        return
    with open(REPOS_FILE) as f:
        lines = f.readlines()
    with open(REPOS_FILE, 'w') as f:
        for l in lines:
            if name not in l:
                f.write(l)

def install_from_repos(pkg):
    if not os.path.exists(REPOS_FILE):
        print("No repos")
        return
    with open(REPOS_FILE) as f:
        repos = [r.strip().rstrip('/') for r in f]
    for r in repos:
        url = f"{r}/{pkg}.ucn"
        try:
            tmp = os.path.join("/tmp", f"{pkg}.ucn")
            urllib.request.urlretrieve(url, tmp)
            install_ucn(tmp)
            os.remove(tmp)
            return
        except:
            continue
    print(f"{pkg} not found in repos")

def remove_package(pkg):
    path = os.path.join(PKG_BASE_DIR, pkg)
    if os.path.exists(path):
        shutil.rmtree(path)
    else:
        print(f"{pkg} not installed")

def update_package(pkg):
    path = os.path.join(PKG_BASE_DIR, pkg)
    if os.path.exists(path):
        gitd = os.path.join(path, '.git')
        if os.path.exists(gitd):
            os.chdir(path)
            run_sudo(["git", "pull"])
    else:
        print(f"{pkg} not installed")

def main():
    if len(sys.argv) < 3:
        print("Usage: install <.ucn|url|pkg> | install --from-repos <pkg> | run <pkg> | remove <pkg> | update <pkg> | add-repo <url> | remove-repo <name>")
        return
    cmd = sys.argv[1]
    if cmd == 'install' and len(sys.argv) == 4 and sys.argv[2] == '--from-repos':
        install_from_repos(sys.argv[3])
    elif cmd == 'install' and sys.argv[2].endswith('.ucn'):
        install_ucn(sys.argv[2])
    elif cmd == 'install' and sys.argv[2].startswith('http'):
        url = sys.argv[2]
        name = os.path.basename(url.rstrip('/')).replace('.git', '')
        target = os.path.join(PKG_BASE_DIR, name)
        if os.path.exists(target):
            os.chdir(target)
            run_sudo(["git", "pull"])
        else:
            run_sudo(["git", "clone", url, target])
    elif cmd == 'install':
        install_from_repos(sys.argv[2])
    elif cmd == 'run':
        run_ucn(sys.argv[2])
    elif cmd == 'remove':
        remove_package(sys.argv[2])
    elif cmd == 'update':
        update_package(sys.argv[2])
    elif cmd == 'add-repo':
        add_repo(sys.argv[2])
    elif cmd == 'remove-repo':
        remove_repo(sys.argv[2])
    else:
        print(f"Unknown: {cmd}")

if __name__ == '__main__':
    main()
