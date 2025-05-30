


# UCN (Universal Compressed eNvironment) Package Manager

UCN is a simple, user-centric package manager designed to manage and run applications organized as packages on your system. It provides an easy way to install, update, remove, and run packages from local files or remote repositories.

---

## Features

- Install packages from local `.ucn` files or remote repositories  
- Execute packages directly using their defined startup commands  
- Add or remove package repositories  
- Organize installed packages under your home directory for easy management  

---

## Installation & Integration

To integrate UCN into your system, you typically:

1. Place the `ucn` executable in a directory included in your system's `PATH` (e.g., `/usr/local/bin`).  
2. Create a folder for your installed packages in your home directory:  
   ```bash
   mkdir -p ~/.ucndata/packages

3. Optionally, create a file to store your configured repositories:

   ```bash
   mkdir -p ~/.local/share/ucn-repos
   touch ~/.local/share/ucn-repos/repos.txt
   ```
4. Add repositories using the `add-repo` command.

Once set up, you can manage packages with simple commands.

---

## Default Repository

UCN does **not** come with pre-configured repositories. The default repository that is commonly used is:

```
https://nikoyandere.github.io/UcnHub
```

You must add this repository explicitly:

```bash
ucn add-repo https://nikoyandere.github.io/UcnHub
```

---

## Usage

```
ucn install <file.ucn|package_name|url>        # Install a package from a local file, repo, or URL  
ucn install --from-repos <package_name>        # Install package from configured repos  
ucn remove <package_name>                       # Remove an installed package  
ucn update <package_name>                       # Update an installed package (git-based)  
ucn add-repo <repo_url>                         # Add a package repository  
ucn remove-repo <repo_name>                     # Remove a package repository  
ucn run <package_name>                          # Run the installed package using its manifest's exec command  
```

---

## Package Location

Installed packages are stored under:

```
~/.ucndata/packages/
```

Each package is extracted into its own directory within this path.

---

## Manifest File

Each package contains a manifest file (`*.ucn-manifest`) with metadata, dependencies, and an executable command. UCN uses this manifest to install dependencies and run the package.

---

## License

This project is licensed under the NLv2,See the [LICENSE](LICENSE) file for details.

---
