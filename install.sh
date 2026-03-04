#!/bin/bash

# Smart Rover AI Tutor - Installation Script for Linux ARM (Debian)
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

# Step 1: Check for Debian-based system
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

# Step 2b: Check required tools for installation
check_prerequisites() {
    print_step "Checking required tools..."

    MISSING_TOOLS=()

    if ! command -v curl >/dev/null 2>&1; then
        MISSING_TOOLS+=("curl")
    fi

    if ! command -v unzip >/dev/null 2>&1; then
        MISSING_TOOLS+=("unzip")
    fi

    if [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
        print_success "All required tools are available (curl, unzip)"
        return 0
    else
        print_error "Missing required tools: ${MISSING_TOOLS[*]}"
        print_error "Install with: sudo apt-get install ${MISSING_TOOLS[*]}"
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

    # Create temporary directory for download and extraction
    TEMP_DIR=$(mktemp -d)
    TEMP_ZIP="$TEMP_DIR/kirocli.zip"

    # Set up cleanup trap
    trap 'rm -rf "$TEMP_DIR"' EXIT INT TERM

    # Download zip package (musl build for maximum compatibility)
    print_step "Downloading kirocli-aarch64-linux-musl.zip..."
    if curl --proto '=https' --tlsv1.2 -sSf \
        'https://desktop-release.q.us-east-1.amazonaws.com/latest/kirocli-aarch64-linux-musl.zip' \
        -o "$TEMP_ZIP"; then
        print_success "Downloaded kirocli-aarch64-linux-musl.zip"
    else
        print_error "Failed to download kirocli-aarch64-linux-musl.zip"
        rm -rf "$TEMP_DIR"
        return 1
    fi

    # Extract zip file
    print_step "Extracting kirocli package..."
    if unzip -q "$TEMP_ZIP" -d "$TEMP_DIR"; then
        print_success "Extracted kirocli package"
    else
        print_error "Failed to extract kirocli package"
        rm -rf "$TEMP_DIR"
        return 1
    fi

    # Verify extracted directory exists
    if [[ ! -d "$TEMP_DIR/kirocli" ]] || [[ ! -f "$TEMP_DIR/kirocli/install.sh" ]]; then
        print_error "Expected kirocli/install.sh not found in extracted package"
        rm -rf "$TEMP_DIR"
        return 1
    fi

    # Run installation script
    print_step "Running kirocli installation script..."
    cd "$TEMP_DIR/kirocli" || {
        print_error "Failed to change to kirocli directory"
        rm -rf "$TEMP_DIR"
        return 1
    }

    # Make install.sh executable and run it
    chmod +x install.sh
    echo ""
    if ./install.sh; then
        echo ""
        print_success "kirocli installation script completed"
    else
        echo ""
        print_error "kirocli installation script failed"
        cd "$SCRIPT_DIR"
        rm -rf "$TEMP_DIR"
        return 1
    fi

    # Return to original directory
    cd "$SCRIPT_DIR"

    # Clean up temporary directory
    rm -rf "$TEMP_DIR"

    # Verify installation
    # The kirocli installer adds ~/.local/bin to PATH in shell configs
    export PATH="$HOME/.local/bin:$PATH"

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

        print_warning "Note: You may need to restart your terminal or run 'source ~/.bashrc' for kiro-cli to be available"

        return 0
    else
        print_error "kiro-cli installation verification failed"
        print_warning "The installer may have succeeded but kiro-cli is not in PATH yet"
        print_warning "Try: export PATH=\"\$HOME/.local/bin:\$PATH\" or restart your terminal"
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
    THONNY_LIB_DIR="$HOME/.config/Thonny/plugins/lib"

    # Check source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        print_error "thonnycontrib directory not found at: $SOURCE_DIR"
        return 1
    fi

    # Initialize tracking variables
    INSTALLED_COUNT=0
    INSTALLED_VERSIONS=()

    print_step "Detecting and installing to all Python versions in Thonny..."

    # Install to all detected Python versions
    for version in 3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7; do
        VERSION_DIR="$THONNY_LIB_DIR/python$version"

        # Check if this Python version's site-packages directory exists
        if [[ -d "$VERSION_DIR/site-packages" ]]; then
            DEST_DIR="$VERSION_DIR/site-packages/thonnycontrib"

            print_step "Installing to Python $version..."

            # Create parent directory if needed
            mkdir -p "$(dirname "$DEST_DIR")"

            # Remove existing destination if it exists
            if [[ -d "$DEST_DIR" ]]; then
                print_warning "Removing existing thonnycontrib for Python $version"
                rm -rf "$DEST_DIR"
            fi

            # Copy directory
            if cp -r "$SOURCE_DIR" "$DEST_DIR"; then
                FILE_COUNT=$(find "$DEST_DIR" -type f -name "*.py" | wc -l)

                # Verify key files exist
                if [[ -f "$DEST_DIR/smart_rover/__init__.py" ]]; then
                    print_success "Installed to Python $version ($FILE_COUNT .py files)"
                    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
                    INSTALLED_VERSIONS+=("$version")
                else
                    print_error "Plugin entry point missing after copy to Python $version"
                fi
            else
                print_error "Failed to copy to Python $version"
            fi
        fi
    done

    # Ensure Python 3.11 is always installed (even if directory didn't exist)
    PYTHON_311_DIR="$THONNY_LIB_DIR/python3.11/site-packages"
    PYTHON_311_DEST="$PYTHON_311_DIR/thonnycontrib"

    # Check if we already installed to 3.11 in the loop above
    ALREADY_INSTALLED_311=false
    for installed_ver in "${INSTALLED_VERSIONS[@]}"; do
        if [[ "$installed_ver" == "3.11" ]]; then
            ALREADY_INSTALLED_311=true
            break
        fi
    done

    if [[ "$ALREADY_INSTALLED_311" == false ]]; then
        print_step "Ensuring Python 3.11 installation (guaranteed)..."

        # Create directory structure if it doesn't exist
        mkdir -p "$PYTHON_311_DIR"

        # Remove existing destination if it exists
        if [[ -d "$PYTHON_311_DEST" ]]; then
            print_warning "Removing existing thonnycontrib for Python 3.11"
            rm -rf "$PYTHON_311_DEST"
        fi

        # Copy directory
        if cp -r "$SOURCE_DIR" "$PYTHON_311_DEST"; then
            FILE_COUNT=$(find "$PYTHON_311_DEST" -type f -name "*.py" | wc -l)

            # Verify key files exist
            if [[ -f "$PYTHON_311_DEST/smart_rover/__init__.py" ]]; then
                print_success "Installed to Python 3.11 [guaranteed] ($FILE_COUNT .py files)"
                INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
                INSTALLED_VERSIONS+=("3.11")
            else
                print_error "Plugin entry point missing after copy to Python 3.11"
            fi
        else
            print_error "Failed to copy to Python 3.11"
        fi
    fi

    # Report installation results
    if [[ $INSTALLED_COUNT -eq 0 ]]; then
        print_error "Failed to install thonnycontrib to any Python version"
        return 1
    elif [[ $INSTALLED_COUNT -eq 1 ]]; then
        print_success "Installed thonnycontrib to 1 Python version: ${INSTALLED_VERSIONS[*]}"
        return 0
    else
        print_success "Installed thonnycontrib to $INSTALLED_COUNT Python versions: ${INSTALLED_VERSIONS[*]}"
        return 0
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
    echo "║  Smart Rover AI Tutor - Linux ARM Installation Script           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    check_debian
    check_prerequisites
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

    echo ""
    read -p "Press Enter to close this window..."
    exit $EXIT_CODE
}

# Run main installation
main
