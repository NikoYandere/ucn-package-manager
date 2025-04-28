import os
import sys
import subprocess

def detect_package_manager():
    if os.path.exists("/usr/bin/apt"):
        return "sudo apt install -y"
    elif os.path.exists("/usr/bin/dnf"):
        return "sudo dnf install -y"
    elif os.path.exists("/usr/bin/pacman"):
        return "sudo pacman -S --noconfirm"
    else:
        return None

def check_pip():
    try:
        subprocess.run(["pip3", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_pip():
    print("pip3 não encontrado. Instalando...")
    package_manager = detect_package_manager()
    if package_manager:
        if "apt" in package_manager:
            os.system("sudo apt update")
            os.system("sudo apt install -y python3-pip")
        elif "dnf" in package_manager:
            os.system("sudo dnf install -y python3-pip")
        elif "pacman" in package_manager:
            os.system("sudo pacman -S --noconfirm python-pip")
        else:
            print("Gerenciador de pacotes não suportado para instalar o pip3.")
    else:
        print("Nenhum gerenciador de pacotes detectado.")

def install_dependencies(system_dependencies, pip_dependencies):
    if system_dependencies:
        installer = detect_package_manager()
        if installer:
            print(f"Instalando dependências de sistema: {' '.join(system_dependencies)}")
            os.system(f"{installer} {' '.join(system_dependencies)}")
        else:
            print("Nenhum gerenciador de pacotes conhecido encontrado.")
    if pip_dependencies:
        if not check_pip():
            install_pip()
        print(f"Instalando dependências pip: {' '.join(pip_dependencies)}")
        os.system(f"pip3 install {' '.join(pip_dependencies)}")

def clone_repository(url):
    repo_name = url.split("/")[-1]
    print(f"Clonando repositório de {url}...")
    os.system(f"git clone {url} ~/{repo_name}")

def main():
    if len(sys.argv) < 3:
        print("Usage: install <package.ucn|url> | update <package.ucn|url>")
        sys.exit(1)

    command = sys.argv[1]
    target = sys.argv[2]

    if command not in ["install", "update"]:
        print("Usage: install <package.ucn|url> | update <package.ucn|url>")
        sys.exit(1)

    if target.startswith("http://") or target.startswith("https://"):
        clone_repository(target)
        sys.exit(0)

    if not os.path.exists(target):
        print(f"Arquivo {target} não encontrado.")
        sys.exit(1)

    url = None
    system_dependencies = []
    pip_dependencies = []

    with open(target, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("url:"):
                url = line.split("url:")[1].strip()
            elif line.startswith("dependencies=system:"):
                deps = line.split("dependencies=system:")[1].strip()
                system_dependencies.extend(deps.split())
            elif line.startswith("dependencies=pip:"):
                deps = line.split("dependencies=pip:")[1].strip()
                pip_dependencies.extend(deps.split())

    if not url:
        print("URL não encontrada no arquivo .ucn.")
        sys.exit(1)

    install_dependencies(system_dependencies, pip_dependencies)
    clone_repository(url)

if __name__ == "__main__":
    main()

