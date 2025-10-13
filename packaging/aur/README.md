# AUR Package for Barones Free Space Cleaner

This directory contains the PKGBUILD and related files for the Arch User Repository (AUR) package.

## Installation from AUR

Once published to AUR, users can install using an AUR helper:

```bash
# Using yay
yay -S barones-free-space-cleaner

# Using paru
paru -S barones-free-space-cleaner
```

## Manual Installation

```bash
# Clone this directory
git clone https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner.git
cd Barones-Free-Space-Cleaner/packaging/aur

# Build and install
makepkg -si
```

## Publishing to AUR

To publish this package to AUR:

1. Create an account on https://aur.archlinux.org/
2. Set up SSH keys for AUR
3. Clone the AUR repository:
   ```bash
   git clone ssh://aur@aur.archlinux.org/barones-free-space-cleaner.git aur-repo
   ```
4. Copy PKGBUILD, .SRCINFO, and related files to the aur-repo directory
5. Commit and push:
   ```bash
   cd aur-repo
   git add .
   git commit -m "Initial commit"
   git push
   ```

## Files

- **PKGBUILD**: Build script for Arch Linux
- **.SRCINFO**: Metadata file for AUR
- **barones-free-space-cleaner.desktop**: Desktop entry file
- **logo_*.png**: Application icons in various sizes

