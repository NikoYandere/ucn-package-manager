**ucn** is a Python-based package manager that simplifies installing and managing projects. It handles system dependencies, Python dependencies, and Git repository cloning directly from GitHub or other Git-based platforms using `.ucn` files or URLs.

### Features:
- Installs system dependencies via package managers (apt, dnf, pacman).
- Installs Python dependencies with pip.
- Clones repositories from `.ucn` files or URLs.
- Supports install and update commands.

### Usage:
- **Install a package**: `ucn install <package.ucn|url>`
- **Update a package**: `ucn update <package.ucn|url>`

### Supported Package Managers:
- **apt** (Ubuntu/Debian)
- **dnf** (Fedora)
- **pacman** (Arch)

### Unsupported Package Managers:
- **snap**
- **flatpak**
- **nix**

### Installation Prerequisites:
- Python 3 must be installed.
- pip should be available for installing Python dependencies.
an  .ucn is like this



`---UCN PACKAGE MANAGER REF----
name:yanix-launcher 
developer:nikoyandere

publisher: Yanix Launcher Community

url:https://github.com/NikoYandere/yanix-launcher

Comment:an Linux Launcher for Yandere simulator

icon:https://raw.githubusercontent.com/NikoYandere/Yanix-

Launcher/refs/heads/main/binary/data/Yanix-Launcher.png

dependencies-system: python-pygame python-requests tk wine`