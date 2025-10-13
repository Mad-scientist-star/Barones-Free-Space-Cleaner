#!/bin/bash

# Free Space Wipe Installer

echo "Installing Free Space Wipe..."

# Create directories if they don't exist
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications

# Copy the program
cp free-space-wipe.py ~/.local/bin/free-space-wipe
chmod +x ~/.local/bin/free-space-wipe

# Create desktop file
cat > ~/.local/share/applications/free-space-wipe.desktop << EOF
[Desktop Entry]
Name=Free Space Wipe
Comment=Wipe free space on drives
Exec=$HOME/.local/bin/free-space-wipe
Icon=drive-harddisk
Terminal=false
Type=Application
Categories=System;Utility;
EOF

# Copy to desktop
cp ~/.local/share/applications/free-space-wipe.desktop ~/Desktop/
chmod +x ~/Desktop/free-space-wipe.desktop

echo "Installation complete!"
echo "You should see a 'Free Space Wipe' icon on your desktop."
