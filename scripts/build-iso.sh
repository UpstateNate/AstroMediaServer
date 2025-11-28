#!/bin/bash
#
# AstroMediaServer ISO Build Script
# Repacks Ubuntu Server 24.04 LTS with autoinstall configuration
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_DIR}/build"
ISO_DIR="${PROJECT_DIR}/iso"
OUTPUT_DIR="${PROJECT_DIR}/output"

UBUNTU_VERSION="24.04.1"
UBUNTU_ISO_URL="https://releases.ubuntu.com/24.04/ubuntu-${UBUNTU_VERSION}-live-server-amd64.iso"
UBUNTU_ISO_NAME="ubuntu-${UBUNTU_VERSION}-live-server-amd64.iso"
OUTPUT_ISO_NAME="astro-media-server-v0.1.iso"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check for required tools
check_dependencies() {
    log_info "Checking dependencies..."

    local deps=("xorriso" "7z" "wget" "mkisofs")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing[*]}
Install with: sudo apt install xorriso p7zip-full wget genisoimage"
    fi

    log_success "All dependencies found"
}

# Download Ubuntu ISO if not present
download_iso() {
    mkdir -p "$BUILD_DIR"

    if [ -f "${BUILD_DIR}/${UBUNTU_ISO_NAME}" ]; then
        log_info "Ubuntu ISO already exists, skipping download"
        return
    fi

    log_info "Downloading Ubuntu Server ${UBUNTU_VERSION} ISO..."
    wget -O "${BUILD_DIR}/${UBUNTU_ISO_NAME}" "$UBUNTU_ISO_URL" \
        || log_error "Failed to download Ubuntu ISO"

    log_success "Ubuntu ISO downloaded"
}

# Extract ISO contents
extract_iso() {
    log_info "Extracting ISO contents..."

    # Clean previous extraction
    rm -rf "${BUILD_DIR}/iso-extract"
    mkdir -p "${BUILD_DIR}/iso-extract"

    # Extract using 7z
    7z x "${BUILD_DIR}/${UBUNTU_ISO_NAME}" -o"${BUILD_DIR}/iso-extract" \
        || log_error "Failed to extract ISO"

    log_success "ISO extracted"
}

# Inject autoinstall configuration
inject_autoinstall() {
    log_info "Injecting autoinstall configuration..."

    local extract_dir="${BUILD_DIR}/iso-extract"

    # Create autoinstall directory structure
    mkdir -p "${extract_dir}/astro"

    # Copy user-data and meta-data
    cp "${ISO_DIR}/user-data" "${extract_dir}/"
    cp "${ISO_DIR}/meta-data" "${extract_dir}/"

    # Copy astro scripts
    if [ -f "${PROJECT_DIR}/scripts/astro-init.sh" ]; then
        cp "${PROJECT_DIR}/scripts/astro-init.sh" "${extract_dir}/astro/"
    else
        log_warn "astro-init.sh not found, creating placeholder"
        echo "#!/bin/bash" > "${extract_dir}/astro/astro-init.sh"
        echo "echo 'Astro init placeholder'" >> "${extract_dir}/astro/astro-init.sh"
    fi

    if [ -f "${PROJECT_DIR}/scripts/astro-setup.py" ]; then
        cp "${PROJECT_DIR}/scripts/astro-setup.py" "${extract_dir}/astro/"
    else
        log_warn "astro-setup.py not found, creating placeholder"
        echo "#!/usr/bin/env python3" > "${extract_dir}/astro/astro-setup.py"
        echo "print('Astro setup placeholder')" >> "${extract_dir}/astro/astro-setup.py"
    fi

    # Copy systemd service
    if [ -f "${PROJECT_DIR}/services/astro-init.service" ]; then
        cp "${PROJECT_DIR}/services/astro-init.service" "${extract_dir}/astro/"
    else
        log_warn "astro-init.service not found, creating placeholder"
        cat > "${extract_dir}/astro/astro-init.service" << 'EOF'
[Unit]
Description=AstroMediaServer First Boot Setup
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/astro/astro-init.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    fi

    # Modify GRUB to enable autoinstall
    if [ -f "${extract_dir}/boot/grub/grub.cfg" ]; then
        log_info "Modifying GRUB configuration for autoinstall..."
        sed -i 's|---|autoinstall ---|g' "${extract_dir}/boot/grub/grub.cfg"
    fi

    # Modify isolinux for BIOS boot (if exists)
    if [ -f "${extract_dir}/isolinux/txt.cfg" ]; then
        log_info "Modifying isolinux configuration for autoinstall..."
        sed -i 's|---|autoinstall ---|g' "${extract_dir}/isolinux/txt.cfg"
    fi

    log_success "Autoinstall configuration injected"
}

# Rebuild ISO
rebuild_iso() {
    log_info "Rebuilding ISO..."

    mkdir -p "$OUTPUT_DIR"

    local extract_dir="${BUILD_DIR}/iso-extract"

    # Generate new ISO using xorriso
    xorriso -as mkisofs \
        -r -V "AstroMediaServer" \
        -o "${OUTPUT_DIR}/${OUTPUT_ISO_NAME}" \
        -J -joliet-long \
        -b boot/grub/i386-pc/eltorito.img \
        -c boot.catalog \
        -no-emul-boot \
        -boot-load-size 4 \
        -boot-info-table \
        --grub2-boot-info \
        --grub2-mbr "${extract_dir}/boot/grub/i386-pc/boot_hybrid.img" \
        -eltorito-alt-boot \
        -e 'boot/grub/efi.img' \
        -no-emul-boot \
        -isohybrid-gpt-basdat \
        "$extract_dir" \
        2>/dev/null || {
            # Fallback method if first attempt fails
            log_warn "Primary method failed, trying fallback..."
            xorriso -as mkisofs \
                -r -V "AstroMediaServer" \
                -o "${OUTPUT_DIR}/${OUTPUT_ISO_NAME}" \
                -J -joliet-long \
                "$extract_dir"
        }

    log_success "ISO created: ${OUTPUT_DIR}/${OUTPUT_ISO_NAME}"
}

# Cleanup build artifacts
cleanup() {
    log_info "Cleaning up build artifacts..."
    rm -rf "${BUILD_DIR}/iso-extract"
    log_success "Cleanup complete"
}

# Main build process
main() {
    echo ""
    echo "=============================================="
    echo "   AstroMediaServer ISO Build Script"
    echo "=============================================="
    echo ""

    check_dependencies
    download_iso
    extract_iso
    inject_autoinstall
    rebuild_iso

    if [ "${1:-}" != "--keep-build" ]; then
        cleanup
    fi

    echo ""
    echo "=============================================="
    log_success "Build complete!"
    echo "  Output: ${OUTPUT_DIR}/${OUTPUT_ISO_NAME}"
    echo "=============================================="
    echo ""
}

# Run main with all arguments
main "$@"
