ucn is a simple Python-based package manager that allows you to install and manage your projects with ease. It can install dependencies and clone repositories directly from GitHub or other Git-based platforms using a .ucn file or a direct URL.
Features

    **Installs system dependencies using supported package managers.**

    Installs Python dependencies using pip.

    Clones repositories from URLs or .ucn files.

    Supports installation and update commands.
Usage
Install

To install a package or project:

    *ucn install <package.ucn|url>

    <package.ucn>: Path to a .ucn file.

    <url>: Direct URL to a GitHub or other Git-based repository.

Update

To update an installed package:

ucn update <package.ucn|url>

Supported Package Managers

ucn supports the following system package managers for installing system dependencies:

    apt (Ubuntu/Debian-based distributions)

    dnf (Fedora-based distributions)

    pacman (Arch-based distributions)

These are the supported package managers for installing system dependencies.
Unsupported Package Managers

ucn does not support the following package managers:

    snap (Snap package manager)

    flatpak (Flatpak package manager)

    nix (Nix package manager)

Currently, ucn does not have the ability to install packages via Snap, Flatpak, or Nix package managers.
Installation
Prerequisites

    Python 3 must be installed on your system.

    pip should be available for installing Python dependencies.
