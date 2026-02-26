# Smart Rover AI Tutor

An AI-powered tutor plugin for Thonny IDE that helps students learn programming with the Smart Factory Rover.

## Installation

### Using Desktop Launcher (Linux)

1. Double-click `smart-rover-installer.desktop` to launch the installer
2. The installation script will run in a terminal window
3. Follow the on-screen instructions
4. Press Enter when complete to close the terminal

### Manual Installation (Linux)

```bash
bash install.sh
```

The installer will:
- Install kiro-cli for AI interactions
- Copy Steering configuration to `~/.kiro/steering`
- Install Thonny plugin to `~/.config/Thonny/plugins/`
- Configure kiro-cli settings

### After Installation

1. Launch Thonny IDE
2. Open **Tools → Kiro**
3. Click **Login** to authenticate with kiro-cli
4. Start using the Smart Rover AI Tutor!

### Installation Notes

- kiro-cli is installed to `~/.local/bin/`
- You may need to restart your terminal or run `source ~/.bashrc` after installation
- The installer requires `curl` and `unzip` commands (install via: `sudo apt-get install curl unzip`)
- The installer uses the musl build for maximum compatibility across all systems

## Uninstallation

To completely remove Smart Rover AI Tutor from your system:

### Option 1: Using the Uninstall Script

1. Navigate to the repository directory
2. Run the uninstallation script:
   ```bash
   chmod +x uninstall.sh
   ./uninstall.sh
   ```

### Option 2: Using the Desktop Launcher (if available)

Double-click the `smart-rover-uninstaller.desktop` file and follow the prompts.

### What Gets Removed

The uninstaller removes:
- **kiro-cli binary**: Complete removal from ~/.local/bin/
- **Configuration directory**: `~/.kiro/` including credentials, settings, and conversation history
- **Thonny plugin**: All Python version installations in `~/.config/Thonny/plugins/`
- **Empty directories**: Cleanup of empty parent directories

**Note**: Thonny IDE itself is not removed. To remove Thonny:
```bash
sudo apt remove thonny
```

### Manual Uninstallation

If the script doesn't work or you prefer manual removal:

```bash
# Remove kiro-cli
kiro-cli uninstall
# Or manually:
rm -rf ~/.local/bin/kiro-cli

# Remove configuration and data
rm -rf ~/.kiro/

# Remove Thonny plugin (check your Python version)
rm -rf ~/.config/Thonny/plugins/lib/python*/site-packages/thonnycontrib/smart_rover/

# Remove desktop launcher files (if copied manually)
rm ~/.local/share/applications/smart-rover-*.desktop
rm ~/Desktop/smart-rover-*.desktop
```