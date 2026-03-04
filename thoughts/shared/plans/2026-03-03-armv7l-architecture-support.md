# Remove Architecture Gate from Install/Uninstall Scripts

## Overview

Remove the `check_architecture()` function from both `install.sh` and `uninstall.sh`. The scripts currently gate on aarch64/arm64 and warn on other architectures. Simply remove this check so the scripts run on any system without an architecture warning. The existing hardcoded download URL stays as-is.

## Current State

- **install.sh:36-47**: `check_architecture()` checks for aarch64/arm64, warns on anything else
- **uninstall.sh:43-55**: Same check (informational only)
- Both scripts call `check_architecture` in `main()`
- Both scripts have "ARM64" in headers/banners

## Desired End State

- `check_architecture()` removed from both scripts
- Scripts run on any architecture without warnings
- Download URL unchanged (`kirocli-aarch64-linux-musl.zip`)
- Headers updated from "ARM64" to "ARM"

## What We're NOT Doing

- Changing the download URL or making it dynamic
- Adding architecture detection logic
- Modifying `.desktop` files or Thonny plugin

## Phase 1: Update install.sh

### Changes:

1. **Update header comment** (`install.sh:3`): Change "ARM64" to "ARM"
2. **Delete `check_architecture()` function** (`install.sh:35-47`)
3. **Remove `check_architecture` call from `main()`** (`install.sh:362`)
4. **Update banner in `main()`** (`install.sh:358`): Change "ARM64" to "ARM"

### Success Criteria:

#### Automated Verification:
- [ ] `bash -n install.sh` passes
- [ ] `grep -c "check_architecture" install.sh` returns 0

#### Manual Verification:
- [ ] On armv7l: script runs without architecture warning
- [ ] On aarch64: no regression

---

## Phase 2: Update uninstall.sh

### Changes:

1. **Update header comment** (`uninstall.sh:3`): Change "ARM64" to "ARM"
2. **Delete `check_architecture()` function** (`uninstall.sh:43-55`)
3. **Remove `check_architecture` call from `main()`** (`uninstall.sh:297`)
4. **Update banner in `main()`** (`uninstall.sh:279`): Change "ARM64" to "ARM"

### Success Criteria:

#### Automated Verification:
- [ ] `bash -n uninstall.sh` passes
- [ ] `grep -c "check_architecture" uninstall.sh` returns 0

#### Manual Verification:
- [ ] On armv7l: uninstall runs without architecture warning
- [ ] On aarch64: no regression

## References

- `install.sh`
- `uninstall.sh`
