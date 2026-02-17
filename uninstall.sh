#!/bin/bash

# Smart Rover AI Tutor - Uninstallation Script for Linux ARM64 (Debian)
# This script removes kiro-cli, configuration files, and the Thonny plugin

set +e  # Continue on errors
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXIT_CODE=0
ITEMS_REMOVED=0
ITEMS_NOT_FOUND=0

# Color codes for output (matching install.sh)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions (matching install.sh)
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ITEMS_REMOVED=$((ITEMS_REMOVED + 1))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    EXIT_CODE=1
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_not_found() {
    echo -e "${YELLOW}○${NC} $1 (not found, skipping)"
    ITEMS_NOT_FOUND=$((ITEMS_NOT_FOUND + 1))
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
        print_warning "Continuing anyway - uninstallation should work on any architecture"
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
        print_warning "dpkg not found. kiro-cli removal will be skipped."
        return 0
    fi
}

# Step 3: Uninstall kiro-cli package
uninstall_kiro_cli() {
    print_step "Uninstalling kiro-cli package..."

    # Check if kiro-cli is installed
    if ! command -v kiro-cli >/dev/null 2>&1; then
        print_not_found "kiro-cli"
        return 0
    fi

    # Get current version before uninstalling
    CURRENT_VERSION=$(kiro-cli --version 2>/dev/null || echo "unknown")
    print_step "Found kiro-cli version: $CURRENT_VERSION"

    # Check if package is installed via dpkg
    if ! dpkg -l kiro-cli >/dev/null 2>&1; then
        print_warning "kiro-cli command exists but package not found in dpkg"
        print_warning "May have been installed manually - cannot remove automatically"
        return 1
    fi

    # Uninstall package using kiro-cli uninstall command
    print_step "Running kiro-cli uninstall..."
    if kiro-cli uninstall >/dev/null 2>&1; then
        print_success "kiro-cli uninstall completed"
    else
        print_error "Failed to run kiro-cli uninstall"
        print_warning "Try manually: kiro-cli uninstall"
        return 1
    fi

    # Verify removal
    if ! command -v kiro-cli >/dev/null 2>&1; then
        print_success "Verified kiro-cli is no longer available"
        return 0
    else
        print_warning "kiro-cli command still exists after removal"
        print_warning "May be installed in multiple locations"
        return 1
    fi
}

# Step 4: Remove .kiro directory (includes steering config, credentials, settings, conversation history)
remove_kiro_directory() {
    print_step "Removing ~/.kiro/ directory..."

    KIRO_DIR="$HOME/.kiro"

    # Check if directory exists
    if [[ ! -d "$KIRO_DIR" ]]; then
        print_not_found "~/.kiro/ directory"
        return 0
    fi

    # Count files before removal
    FILE_COUNT=$(find "$KIRO_DIR" -type f 2>/dev/null | wc -l)
    DIR_SIZE=$(du -sh "$KIRO_DIR" 2>/dev/null | cut -f1)

    print_step "Found ~/.kiro/ directory ($FILE_COUNT files, $DIR_SIZE)"
    print_warning "This will remove all kiro-cli data including:"
    print_warning "  - Steering configuration"
    print_warning "  - Authentication credentials"
    print_warning "  - Settings and preferences"
    print_warning "  - Conversation history"

    # Remove directory
    if rm -rf "$KIRO_DIR" 2>/dev/null; then
        print_success "Removed ~/.kiro/ directory ($FILE_COUNT files)"

        # Verify removal
        if [[ ! -d "$KIRO_DIR" ]]; then
            return 0
        else
            print_error "Directory still exists after removal"
            return 1
        fi
    else
        print_error "Failed to remove ~/.kiro/ directory"
        print_warning "Try manually: rm -rf ~/.kiro"
        return 1
    fi
}

# Step 5: Remove thonnycontrib plugin from all Python versions
remove_thonnycontrib() {
    print_step "Removing thonnycontrib plugin from Thonny..."

    THONNY_LIB_DIR="$HOME/.config/Thonny/plugins/lib"
    FOUND_ANY=false
    REMOVED_COUNT=0

    # Check if Thonny plugins directory exists
    if [[ ! -d "$THONNY_LIB_DIR" ]]; then
        print_not_found "Thonny plugins directory"
        return 0
    fi

    # Check all Python versions from 3.15 down to 3.7
    for version in 3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7; do
        PLUGIN_DIR="$THONNY_LIB_DIR/python$version/site-packages/thonnycontrib"

        if [[ -d "$PLUGIN_DIR" ]]; then
            FOUND_ANY=true
            FILE_COUNT=$(find "$PLUGIN_DIR" -type f -name "*.py" 2>/dev/null | wc -l)

            print_step "Found plugin in Python $version ($FILE_COUNT .py files)"

            # Remove thonnycontrib directory
            if rm -rf "$PLUGIN_DIR" 2>/dev/null; then
                print_success "Removed plugin from Python $version"
                REMOVED_COUNT=$((REMOVED_COUNT + 1))

                # Verify removal
                if [[ -d "$PLUGIN_DIR" ]]; then
                    print_error "Plugin directory still exists after removal"
                fi
            else
                print_error "Failed to remove plugin from Python $version"
                print_warning "Try manually: rm -rf $PLUGIN_DIR"
            fi
        fi
    done

    if [[ "$FOUND_ANY" == false ]]; then
        print_not_found "thonnycontrib plugin in any Python version"
        return 0
    fi

    if [[ $REMOVED_COUNT -gt 0 ]]; then
        print_success "Removed plugin from $REMOVED_COUNT Python version(s)"
        return 0
    else
        print_error "Found plugin(s) but failed to remove any"
        return 1
    fi
}

# Step 6: Check for desktop launcher file
check_desktop_launcher() {
    print_step "Checking for desktop launcher file..."

    # Common desktop file locations
    LOCATIONS=(
        "$HOME/.local/share/applications/smart-rover-installer.desktop"
        "$HOME/Desktop/smart-rover-installer.desktop"
        "/usr/share/applications/smart-rover-installer.desktop"
        "/usr/local/share/applications/smart-rover-installer.desktop"
    )

    FOUND_LOCATIONS=()

    # Check each location
    for location in "${LOCATIONS[@]}"; do
        if [[ -f "$location" ]]; then
            FOUND_LOCATIONS+=("$location")
        fi
    done

    if [[ ${#FOUND_LOCATIONS[@]} -eq 0 ]]; then
        print_not_found "Desktop launcher file"
        return 0
    fi

    # Report found locations
    print_warning "Found desktop launcher file(s) at:"
    for location in "${FOUND_LOCATIONS[@]}"; do
        echo "  - $location"
    done
    print_warning "These were not installed by the installer and should be removed manually if desired"
    print_warning "To remove manually, run:"
    for location in "${FOUND_LOCATIONS[@]}"; do
        echo "    rm \"$location\""
    done

    return 0
}

# Step 7: Clean up empty parent directories
cleanup_empty_dirs() {
    print_step "Cleaning up empty parent directories..."

    CLEANED_ANY=false

    # Remove empty Thonny site-packages directories
    THONNY_LIB_DIR="$HOME/.config/Thonny/plugins/lib"
    if [[ -d "$THONNY_LIB_DIR" ]]; then
        for version in 3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7; do
            SITE_PACKAGES="$THONNY_LIB_DIR/python$version/site-packages"
            if [[ -d "$SITE_PACKAGES" ]] && [[ -z "$(ls -A "$SITE_PACKAGES" 2>/dev/null)" ]]; then
                rmdir "$SITE_PACKAGES" 2>/dev/null && print_success "Removed empty directory: python$version/site-packages"
                CLEANED_ANY=true
            fi

            PYTHON_DIR="$THONNY_LIB_DIR/python$version"
            if [[ -d "$PYTHON_DIR" ]] && [[ -z "$(ls -A "$PYTHON_DIR" 2>/dev/null)" ]]; then
                rmdir "$PYTHON_DIR" 2>/dev/null && print_success "Removed empty directory: python$version"
                CLEANED_ANY=true
            fi
        done
    fi

    if [[ "$CLEANED_ANY" == false ]]; then
        print_not_found "Empty directories to clean up"
    fi

    return 0
}

# Main uninstallation flow
main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Smart Rover AI Tutor - Linux ARM64 Uninstallation Script     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "This will remove:"
    echo "  • kiro-cli package (complete removal)"
    echo "  • ~/.kiro/ directory (configuration, credentials, history)"
    echo "  • Thonny plugin files (all Python versions)"
    echo ""
    echo "WARNING: This operation cannot be undone!"
    echo ""
    read -p "Do you want to continue? (yes/no): " -r REPLY
    echo ""

    if [[ ! "$REPLY" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Uninstallation cancelled by user."
        exit 0
    fi

    check_architecture
    check_debian
    uninstall_kiro_cli
    remove_kiro_directory
    remove_thonnycontrib
    check_desktop_launcher
    cleanup_empty_dirs

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "║  ${GREEN}✓ Uninstallation completed successfully!${NC}                       ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Summary:"
        echo "  • Items removed: $ITEMS_REMOVED"
        echo "  • Items not found: $ITEMS_NOT_FOUND"
        echo ""
        echo "Smart Rover AI Tutor has been completely removed from your system."

        if command -v thonny >/dev/null 2>&1; then
            echo ""
            echo "Note: Thonny IDE is still installed. If you want to remove it:"
            echo "  sudo apt remove thonny"
        fi
    else
        echo "║  ${YELLOW}⚠ Uninstallation completed with some errors${NC}                    ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Summary:"
        echo "  • Items removed: $ITEMS_REMOVED"
        echo "  • Items not found: $ITEMS_NOT_FOUND"
        echo ""
        echo "Please review the error messages above and clean up manually if needed."
    fi

    echo ""
    read -p "Press Enter to close this window..."
    exit $EXIT_CODE
}

# Run main uninstallation
main
