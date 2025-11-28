# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AstroMediaServer (AMS) is a custom Linux distribution that deploys a turnkey home media server stack on commodity hardware. It uses Ubuntu Server 24.04 LTS as the base with Docker containers for all services.

**Current Status:** Planning phase - only the project charter (README.md) exists.

## Architecture

- **Installation Method:** Ubuntu Autoinstall (Cloud-Init) with `user-data` YAML injection
- **Post-Install Automation:** systemd oneshot service triggers `astro-init` on first boot
- **Configuration UI:** Whiptail-based TUI wizard (`astro-setup.py`)
- **Orchestration:** Docker Compose v2 with dynamic `docker-compose.yml` generation
- **Container Sources:** Docker Hub / LinuxServer.io (LSIO)

## Development Phases

1. **Phase 1:** Create bootable ISO with hands-free Ubuntu install → `user-data` YAML
2. **Phase 2:** TUI wizard and Docker Compose generator → `astro-setup.py`
3. **Phase 3:** Integrate script into ISO with systemd trigger → `astro-media-server-v0.1.iso`
4. **Phase 4:** ASCII art, theming, error handling → Release Candidate

## Key Technical Decisions

- Default user: `astro-admin`
- Directory structure: `/opt/astro/{config,media,torrents,usenet}`
- All state persists in Docker volumes (OS is disposable)
- Services pulled at runtime (no proprietary binaries in ISO)

## Application Stack

User selects from these options during setup:
- **Media Server:** Plex / Jellyfin / Emby
- **Downloader:** SABnzbd / NZBGet / QBit
- **Gateway:** Traefik / NPM
- **Dashboard:** Homepage / Heimdall
- **Always included:** Radarr, Sonarr, Lidarr, Readarr, Prowlarr, Watchtower

## Base Packages

Installed via autoinstall: `docker.io`, `docker-compose-v2`, `python3`, `whiptail`, `git`, `curl`
