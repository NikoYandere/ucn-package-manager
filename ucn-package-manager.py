#!/usr/bin/env python3
import os
import sys
import subprocess
import zipfile
import shutil
import urllib.request
from urllib.error import URLError

HOME = os.path.expanduser("~")
REPOS_FILE = os.path.join(HOME, ".local", "share", "ucn-repos", "repos.txt")
PKG_BASE_DIR = os.path.join(HOME, ".ucndata", "packages")
PM_COMMANDS = {
    "apt":    {"update": ["apt", "update"],     "install": ["apt", "install", "-y"]},
    "dnf":    {"update": ["dnf", "makecache"],  "install": ["dnf", "install", "-y"]},
    "zypper": {"update": ["zypper", "refresh"],  "install": ["zypper", "install", "-y"]},
    "pacman":{"update": ["pacman", "-Sy"],      "install": ["pacman", "-S", "--noconfirm"]},
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

def parse_manifest(text):
    meta, deps = {}, {}
    lines = text.splitlines()
    section = None
    acc = []
    last_key = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        if ':' in line and section is None:
            k, v = line.split(':', 1)
            meta[k.lower().strip()] = v.strip()
        elif line.lower() == 'dependencies':
            section = 'deps'
        elif section == 'deps':
            if line.startswith('(') and line.endswith(')'):
                if acc and last_key:
                    deps[last_key] = acc
                last_key = line[1:-1].lower()
                acc = []
            elif line:
                acc.extend(line.split())
    if section == 'deps' and acc and last_key:
        deps[last_key] = acc
    meta['dependencies'] = deps
    return meta

def install_dependencies(deps):
    pm = detect_package_manager()
    for dtype, pkgs in deps.items():
        if dtype in ('flatpak', 'snap'):
            cmd = [dtype, "install", "-y"] if dtype == 'flatpak' else ["snap", "install"]
            run_sudo(cmd + pkgs)
        elif dtype == 'makepkg':
            cwd = os.getcwd()
            for repo in pkgs:
                run_sudo(["git", "clone", repo])
                d = os.path.basename(repo)
                os.chdir(d)
                run_sudo(["makepkg", "-si"])
                os.chdir(cwd)
        elif dtype == pm:
            cmds = PM_COMMANDS[pm]
            if cmds['update']:
                run_sudo(cmds['update'])
            run_sudo(cmds['install'] + pkgs)

def extract_ucn_package(zip_path, name):
    dest = os.path.join(PKG_BASE_DIR, name)
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        root = next((f.split('/',1)[0] for f in z.namelist() if '/' in f), None)
        for member in z.namelist():
            rel = member[len(root)+1:] if root and member.startswith(root+'/') else member
            if not rel:
                continue
            out = os.path.join(dest, rel)
            if member.endswith('/'):
                os.makedirs(out, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with z.open(member) as src, open(out,'wb') as dst:
                    shutil.copyfileobj(src,dst)

def install_ucn(file_path):
    with zipfile.ZipFile(file_path) as z:
        m = next((f for f in z.namelist() if f.endswith('-manifest')), None)
        if not m:
            print("Manifest not found")
            return
        text = z.read(m).decode()
    meta = parse_manifest(text)
    name = meta.get('name')
    if not name:
        print("Name missing")
        return
    pkg_dir = os.path.join(PKG_BASE_DIR, name)
    if os.path.isdir(pkg_dir):
        print(f"Package {name} already installed")
        return
    if meta['dependencies']:
        install_dependencies(meta['dependencies'])
    extract_ucn_package(file_path, name)
    if meta.get('exec'):
        subprocess.run(meta['exec'], shell=True, check=True, cwd=pkg_dir)

def run_ucn(pkg):
    pkg = pkg[:-4] if pkg.endswith('.ucn') else pkg
    base = os.path.join(PKG_BASE_DIR, pkg)
    if not os.path.isdir(base):
        print(f"Package {pkg} not installed")
        return
    mp=None
    for r, _, fs in os.walk(base):
        for f in fs:
            if f.endswith('-manifest'):
                mp=os.path.join(r, f)
                break
        if mp:
            break
    if not mp:
        print("Manifest not found")
        return
    cmd=parse_manifest(open(mp).read()).get('exec')
    if not cmd:
        print("No exec command")
        return
    subprocess.run(cmd, shell=True, check=True, cwd=base)

def add_repo(url):
    os.makedirs(os.path.dirname(REPOS_FILE), exist_ok=True)
    with open(REPOS_FILE,'a') as f:
        f.write(url.rstrip('/')+"\n")

def remove_repo(name):
    if not os.path.exists(REPOS_FILE):
        return
    lines = open(REPOS_FILE).readlines()
    with open(REPOS_FILE,'w') as f:
        for l in lines:
            if name not in l:
                f.write(l)

def download_with_progress(url, dest, pkg):
    try:
        with urllib.request.urlopen(url) as response:
            total=int(response.getheader('Content-Length','0'))
            downloaded=0
            block_size=8192
            with open(dest,'wb') as f:
                while True:
                    chunk=response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded+=len(chunk)
                    if total:
                        percent=downloaded/total*100
                        bar_len=40
                        filled=int(bar_len*downloaded//total)
                        bar='#'*filled+' '*(bar_len-filled)
                        print(f"\rInstalling [{bar}] {percent:3.0f}% {pkg}",end='',flush=True)
            print()
    except URLError:
        raise

def install_from_repos(pkgs):
    for pkg in pkgs:
        name=pkg[:-4] if pkg.endswith('.ucn') else pkg
        pkg_dir=os.path.join(PKG_BASE_DIR,name)
        if os.path.isdir(pkg_dir):
            print(f"Package {name} already installed")
            continue
        if not os.path.exists(REPOS_FILE):
            print("No repos")
            return
        repos=[r.strip().rstrip('/') for r in open(REPOS_FILE)]
        for r in repos:
            url=f"{r}/{name}.ucn"
            tmp=os.path.join('/tmp',f"{name}.ucn")
            try:
                download_with_progress(url,tmp,name)
                install_ucn(tmp)
                os.remove(tmp)
                break
            except Exception:
                continue
        else:
            print(f"{name} not found in repos")

def remove_package(pkg):
    path=os.path.join(PKG_BASE_DIR,pkg)
    if os.path.exists(path):
        shutil.rmtree(path)
    else:
        print(f"{pkg} not installed")

def update_package(pkg):
    path=os.path.join(PKG_BASE_DIR,pkg)
    if os.path.exists(path) and os.path.isdir(os.path.join(path,'.git')):
        os.chdir(path)
        run_sudo(["git","pull"])
    else:
        print(f"{pkg} not installed or not a git repo")

def list_packages():
    if not os.path.isdir(PKG_BASE_DIR):
        print("No packages installed.")
        return
    pkgs=sorted(os.listdir(PKG_BASE_DIR))
    if not pkgs:
        print("No packages installed.")
    else:
        for p in pkgs:
            print(p)

def main():
    if len(sys.argv)<2:
        print("Usage: install [--from-repos] <pkg1> [<pkg2> ...] | run <pkg> | remove <pkg> | update <pkg> | add-repo <url> | remove-repo <name> | list")
        return
    cmd=sys.argv[1]
    if cmd=='list':
        list_packages()
        return
    if cmd=='install':
        args=sys.argv[2:]
        if args and args[0]=='--from-repos':
            install_from_repos(args[1:])
            return
        for arg in args:
            if arg.endswith('.ucn'):
                install_ucn(arg)
            elif arg.startswith('http'):
                name=os.path.basename(arg.rstrip('/')).replace('.git','')
                tgt=os.path.join(PKG_BASE_DIR,name)
                if os.path.exists(tgt):
                    os.chdir(tgt)
                    run_sudo(["git","pull"])
                else:
                    run_sudo(["git","clone",arg,tgt])
            else:
                install_from_repos([arg])
        return
    if cmd=='run':
        run_ucn(sys.argv[2])
    elif cmd=='remove':
        remove_package(sys.argv[2])
    elif cmd=='update':
        update_package(sys.argv[2])
    elif cmd=='add-repo':
        add_repo(sys.argv[2])
    elif cmd=='remove-repo':
        remove_repo(sys.argv[2])
    else:
        print(f"Unknown: {cmd}")

if __name__=='__main__':
    main()
