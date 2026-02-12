#!/bin/bash

# Smart Rover AI Tutor - Installation Script for Linux ARM64 (Debian)
# This script installs kiro-cli, copies configuration files, and sets up the Thonny plugin

set +e  # Continue on errors
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXIT_CODE=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    EXIT_CODE=1
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Check system architecture
check_architecture() {
    print_step "Checking system architecture..."
    ARCH=$(uname -m)
    if [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        print_success "Detected ARM64 architecture: $ARCH"
        return 0
    else
        print_warning "Expected ARM64 architecture, but detected: $ARCH"
        print_warning "Installation may not work correctly on this system"
        return 0
    fi
}

# Step 2: Check for Debian-based system
check_debian() {
    print_step "Checking for Debian-based system..."
    if command -v dpkg >/dev/null 2>&1; then
        print_success "Debian package manager (dpkg) detected"
        return 0
    else
        print_error "dpkg not found. This script is designed for Debian-based systems."
        return 1
    fi
}

# Step 3: Install or update kiro-cli
install_kiro_cli() {
    print_step "Installing kiro-cli..."

    # Check if kiro-cli is already installed
    IS_INSTALLED=false
    OLD_VERSION="none"
    if command -v kiro-cli >/dev/null 2>&1; then
        IS_INSTALLED=true
        OLD_VERSION=$(kiro-cli --version 2>/dev/null || echo "unknown")
        print_warning "kiro-cli is already installed (version: $OLD_VERSION)"
        print_step "Updating to latest version..."
    fi

    # Download .deb package
    print_step "Downloading kiro-cli.deb..."
    TEMP_DEB=$(mktemp)
    if wget -q --show-progress https://desktop-release.q.us-east-1.amazonaws.com/latest/kiro-cli.deb -O "$TEMP_DEB"; then
        print_success "Downloaded kiro-cli.deb"
    else
        print_error "Failed to download kiro-cli.deb"
        rm -f "$TEMP_DEB"
        return 1
    fi

    # Install package
    print_step "Installing kiro-cli package..."
    if sudo dpkg -i "$TEMP_DEB" 2>/dev/null; then
        print_success "kiro-cli package installed"
    else
        print_warning "dpkg reported errors, attempting to fix dependencies..."
        if sudo apt-get install -f -y >/dev/null 2>&1; then
            print_success "Dependencies fixed, kiro-cli installed"
        else
            print_error "Failed to install kiro-cli"
            rm -f "$TEMP_DEB"
            return 1
        fi
    fi

    # Clean up
    rm -f "$TEMP_DEB"

    # Verify installation
    if command -v kiro-cli >/dev/null 2>&1; then
        NEW_VERSION=$(kiro-cli --version 2>/dev/null || echo "installed")
        if [[ "$IS_INSTALLED" == true ]]; then
            if [[ "$OLD_VERSION" == "$NEW_VERSION" ]]; then
                print_success "kiro-cli is up to date (version: $NEW_VERSION)"
            else
                print_success "kiro-cli updated: $OLD_VERSION → $NEW_VERSION"
            fi
        else
            print_success "kiro-cli successfully installed (version: $NEW_VERSION)"
        fi
        return 0
    else
        print_error "kiro-cli installation verification failed"
        return 1
    fi
}

# Step 4: Copy Steering directory
copy_steering() {
    print_step "Copying Steering configuration..."

    SOURCE_DIR="$SCRIPT_DIR/Steering"
    DEST_DIR="$HOME/.kiro/steering"

    # Check source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        print_error "Steering directory not found at: $SOURCE_DIR"
        return 1
    fi

    # Create parent directory if needed
    mkdir -p "$HOME/.kiro"

    # Remove existing destination if it exists
    if [[ -d "$DEST_DIR" ]]; then
        print_warning "Removing existing Steering directory at: $DEST_DIR"
        rm -rf "$DEST_DIR"
    fi

    # Copy directory
    if cp -r "$SOURCE_DIR" "$DEST_DIR"; then
        FILE_COUNT=$(find "$DEST_DIR" -type f | wc -l)
        print_success "Copied Steering directory ($FILE_COUNT files) to: $DEST_DIR"
        return 0
    else
        print_error "Failed to copy Steering directory"
        return 1
    fi
}

# Step 5: Copy thonnycontrib package
copy_thonnycontrib() {
    print_step "Copying thonnycontrib plugin..."

    SOURCE_DIR="$SCRIPT_DIR/thonnycontrib"
    DEST_DIR="$HOME/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib"

    # Check source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        print_error "thonnycontrib directory not found at: $SOURCE_DIR"
        return 1
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$DEST_DIR")"

    # Remove existing destination if it exists
    if [[ -d "$DEST_DIR" ]]; then
        print_warning "Removing existing thonnycontrib directory at: $DEST_DIR"
        rm -rf "$DEST_DIR"
    fi

    # Copy directory
    if cp -r "$SOURCE_DIR" "$DEST_DIR"; then
        FILE_COUNT=$(find "$DEST_DIR" -type f -name "*.py" | wc -l)
        print_success "Copied thonnycontrib package ($FILE_COUNT .py files) to: $DEST_DIR"

        # Verify key files exist
        if [[ -f "$DEST_DIR/smart_rover/__init__.py" ]]; then
            print_success "Verified plugin entry point exists"
            return 0
        else
            print_error "Plugin entry point not found after copy"
            return 1
        fi
    else
        print_error "Failed to copy thonnycontrib directory"
        return 1
    fi
}

# Step 6: Configure kiro-cli settings
configure_kiro_cli() {
    print_step "Configuring kiro-cli settings..."

    # Check if kiro-cli is available
    if ! command -v kiro-cli >/dev/null 2>&1; then
        print_error "kiro-cli not found in PATH, cannot configure settings"
        return 1
    fi

    # Set chat.greeting.enabled to false
    if kiro-cli settings chat.greeting.enabled false >/dev/null 2>&1; then
        print_success "Disabled chat greeting: chat.greeting.enabled = false"
        return 0
    else
        print_warning "Failed to set kiro-cli setting (may require authentication)"
        print_warning "Run manually after login: kiro-cli settings chat.greeting.enabled false"
        return 0
    fi
}

# Main installation flow
main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Smart Rover AI Tutor - Linux ARM64 Installation Script       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    check_architecture
    check_debian
    install_kiro_cli
    copy_steering
    copy_thonnycontrib
    configure_kiro_cli

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "║  ${GREEN}✓ Installation completed successfully!${NC}                         ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Next steps:"
        echo "  1. Launch Thonny IDE"
        echo "  2. Open Tools → Kiro"
        echo "  3. Click 'Login' to authenticate with kiro-cli"
        echo "  4. Start using the Smart Rover AI Tutor!"
    else
        echo "║  ${YELLOW}⚠ Installation completed with some errors${NC}                      ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Please review the error messages above and fix any issues."
        echo "You can re-run this script after resolving the errors."
    fi

    exit $EXIT_CODE
}

# Run main installation
main
