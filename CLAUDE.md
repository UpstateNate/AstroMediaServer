# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AstroMediaServer (AMS) is a custom Linux distribution that deploys a turnkey home media server stack on commodity hardware. It uses Ubuntu Server 24.04 LTS as the base with Docker containers for all services.

**Current Status:** Core implementation complete - TUI wizard, Docker Compose generation, and ISO build system are functional.

## Architecture

- **Installation Method:** Ubuntu Autoinstall (Cloud-Init) with `user-data` YAML injection
- **Post-Install Automation:** systemd oneshot service triggers `astro-init` on first boot
- **Configuration UI:** Whiptail-based TUI wizard (`astro-setup.py`)
- **Orchestration:** Docker Compose v2 with dynamic `docker-compose.yml` generation
- **Container Sources:** Docker Hub / LinuxServer.io (LSIO)
- **Dashboard:** Auto-generated Homepage configuration with service widgets

## Project Structure

```
AstroMediaServer/
├── iso/                    # Autoinstall configuration
│   ├── user-data          # Cloud-init autoinstall config
│   └── meta-data          # Cloud-init metadata
├── scripts/
│   ├── build-iso.sh       # ISO build script
│   ├── astro-init.sh      # First-boot initialization
│   └── astro-setup.py     # TUI wizard & compose generator
├── services/
│   └── astro-init.service # systemd service unit
├── docs/
│   └── CHARTER.md         # Original project specification
└── assets/                # Branding assets (future)
```

## Key Components

### astro-setup.py
Main TUI wizard that:
- Presents whiptail menus for service selection
- Detects hardware transcoding capabilities (NVIDIA/Intel)
- Configures VPN integration (gluetun)
- Generates docker-compose.yml
- Auto-generates Homepage dashboard config

### user-data
Ubuntu Autoinstall configuration:
- Creates `astro-admin` user (password: `astro`)
- Installs Docker, Python, whiptail
- Sets up systemd first-boot trigger

### build-iso.sh
ISO generation script:
- Downloads Ubuntu Server 24.04 ISO
- Injects autoinstall configuration
- Repacks as bootable ISO

## Application Stack

### Core Services (Always Installed)
- **Media Server:** Plex / Jellyfin / Emby
- **Arr Suite:** Radarr, Sonarr, Lidarr, Readarr, Prowlarr
- **Downloader:** qBittorrent / SABnzbd / NZBGet
- **Gateway:** Traefik / Nginx Proxy Manager
- **Dashboard:** Homepage / Heimdall
- **Updates:** Watchtower

### Optional Services
- **Bazarr:** Subtitle management
- **Overseerr:** Media requests
- **Tautulli:** Plex statistics
- **Portainer:** Docker management
- **Gluetun:** VPN for downloaders

## Development Commands

```bash
# Test wizard locally (requires Docker, whiptail)
sudo python3 scripts/astro-setup.py

# Build ISO (requires xorriso, p7zip-full, genisoimage)
./scripts/build-iso.sh

# Keep build artifacts for debugging
./scripts/build-iso.sh --keep-build
```

## Key Technical Decisions

- Default user: `astro-admin` (password: `astro`)
- Directory structure: `/opt/astro/{config,media,torrents,usenet}`
- All state persists in Docker volumes (OS is disposable)
- Services pulled at runtime (no proprietary binaries in ISO)
- Homepage config auto-generated with all selected services
- VPN routes only download client traffic (not media server)
- Hardware transcoding auto-detected and configured

## Future Work

- Backup/restore functionality
- Web-based post-install configuration
- Storage/drive mount wizard
- Arr app API key auto-integration
