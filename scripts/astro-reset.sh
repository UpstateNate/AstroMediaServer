#!/bin/bash
#
# AstroMediaServer Reset Script
# Wipes all containers, configs, and data to start fresh
#

set -euo pipefail

ASTRO_DIR="/opt/astro"
COMPOSE_FILE="${ASTRO_DIR}/docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (sudo)"
    exit 1
fi

echo ""
echo "=============================================="
echo "   AstroMediaServer Reset"
echo "=============================================="
echo ""
log_warn "This will DELETE all AstroMediaServer data:"
echo "  - All Docker containers"
echo "  - All configuration files"
echo "  - All downloaded media"
echo "  - All Docker volumes"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_info "Reset cancelled."
    exit 0
fi

echo ""

# Stop and remove containers
if [ -f "$COMPOSE_FILE" ]; then
    log_info "Stopping and removing containers..."
    cd "$ASTRO_DIR"
    docker compose down -v --remove-orphans 2>/dev/null || true
    log_ok "Containers removed"
else
    log_info "No docker-compose.yml found, skipping compose down"
fi

# Remove any orphaned astro containers by name
log_info "Removing any orphaned containers..."
CONTAINERS="homepage plex jellyfin emby radarr sonarr lidarr prowlarr sabnzbd nzbget qbittorrent traefik nginx-proxy-manager overseerr jellyseerr ombi watchtower heimdall"
for container in $CONTAINERS; do
    docker rm -f "$container" 2>/dev/null || true
done
log_ok "Orphaned containers cleaned up"

# Remove astro directory contents
if [ -d "$ASTRO_DIR" ]; then
    log_info "Removing ${ASTRO_DIR} contents..."
    rm -rf "${ASTRO_DIR:?}"/*
    rm -rf "${ASTRO_DIR:?}"/.*  2>/dev/null || true
    log_ok "Astro directory cleared"
fi

# Ask about Docker images
echo ""
read -p "Remove downloaded Docker images? This saves disk but requires re-download (yes/no): " remove_images
if [ "$remove_images" == "yes" ]; then
    log_info "Removing Docker images..."
    docker system prune -af 2>/dev/null || true
    log_ok "Docker images removed"
fi

echo ""
echo "=============================================="
log_ok "Reset complete!"
echo ""
echo "To reinstall, run:"
echo "  sudo python3 /path/to/astro-setup.py"
echo "=============================================="
echo ""
