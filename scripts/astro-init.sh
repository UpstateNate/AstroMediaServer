#!/bin/bash
#
# AstroMediaServer First Boot Initialization Script
# Runs on first boot to launch the setup wizard
#

set -euo pipefail

ASTRO_DIR="/opt/astro"
LOG_FILE="${ASTRO_DIR}/astro-init.log"
SETUP_SCRIPT="${ASTRO_DIR}/astro-setup.py"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ASCII Art Banner
show_banner() {
    clear
    cat << 'EOF'

        *    .  *       .             *
                   *       *    .        *    .    *
     .   *    .        .        .    *
           .     *                       *
    *   .    *    *        *   .     .     *
        .       .    .            *
  .        .         *    .           .        *
              *            .     *         .

             ___        __
            /   |  ___ / /_ _____ ____
           / /| | / __// __// ___// __ \
          / ___ |(__  ) /_ / /   / /_/ /
         /_/  |_/____/\__//_/    \____/
            __  ___         ___        _____
           /  |/  /___  ___/ (_)__ _  / ___/___  ____ _  _____ ____
          / /|_/ // _ \/ _  / // _ `/ \__ \/ _ \/ __/| |/ / _ \/ __/
         /_/  /_/ \___/\_,_/_/ \_,_/ ___/ /\___/_/   |___/\___/_/
                                   /____/

                   Home Media Empire v0.1

EOF
    echo ""
}

# Log function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"

    case "$level" in
        INFO)  echo -e "${CYAN}[INFO]${NC} ${message}" ;;
        OK)    echo -e "${GREEN}[OK]${NC} ${message}" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} ${message}" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} ${message}" ;;
    esac
}

# Wait for network connectivity
wait_for_network() {
    log "INFO" "Waiting for network connectivity..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
            log "OK" "Network is available"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log "WARN" "Network not available after ${max_attempts} attempts"
    return 1
}

# Wait for Docker to be ready
wait_for_docker() {
    log "INFO" "Waiting for Docker to be ready..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker info &>/dev/null; then
            log "OK" "Docker is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log "ERROR" "Docker not ready after ${max_attempts} attempts"
    return 1
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."

    # Check for required commands
    local cmds=("docker" "python3" "whiptail")
    for cmd in "${cmds[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            log "ERROR" "Required command not found: $cmd"
            return 1
        fi
    done

    # Check for setup script
    if [ ! -f "$SETUP_SCRIPT" ]; then
        log "ERROR" "Setup script not found: $SETUP_SCRIPT"
        return 1
    fi

    log "OK" "All prerequisites met"
    return 0
}

# Main entry point
main() {
    # Create log directory
    mkdir -p "$ASTRO_DIR"

    show_banner

    echo ""
    log "INFO" "AstroMediaServer First Boot Initialization"
    log "INFO" "Log file: $LOG_FILE"
    echo ""

    # Run prerequisite checks
    if ! check_prerequisites; then
        log "ERROR" "Prerequisite check failed"
        echo ""
        echo "Press Enter to continue to login prompt..."
        read -r
        exit 1
    fi

    # Wait for services
    wait_for_network || true  # Continue even if network fails

    if ! wait_for_docker; then
        log "ERROR" "Docker is not available. Please check the installation."
        echo ""
        echo "Press Enter to continue to login prompt..."
        read -r
        exit 1
    fi

    echo ""
    log "INFO" "Starting setup wizard..."
    sleep 2

    # Launch the Python setup wizard
    if python3 "$SETUP_SCRIPT"; then
        log "OK" "Setup completed successfully"
    else
        log "WARN" "Setup wizard exited with non-zero status"
    fi

    # Create completion marker
    touch "${ASTRO_DIR}/.setup-complete"

    log "INFO" "First boot initialization complete"
    echo ""
    echo "Press Enter to continue..."
    read -r
}

# Run main
main "$@"
