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