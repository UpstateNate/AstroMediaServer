<p align="center">
  <img src="assets/images/logo.png" alt="AstroMediaServer Logo" width="400">
</p>

<h1 align="center">AstroMediaServer</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://ubuntu.com/"><img src="https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420?logo=ubuntu&logoColor=white" alt="Ubuntu"></a>
  <a href="https://docs.docker.com/compose/"><img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker"></a>
</p>

<p align="center">
  <strong>A turnkey Linux distribution for deploying your Home Media Empire</strong>
</p>

<p align="center">
  AstroMediaServer (AMS) transforms commodity hardware into a fully-configured media server<br>
  with zero Linux knowledge required. Boot the ISO, answer a few questions, and your personal streaming service is ready.
</p>

## Features

- **Zero-Config Install** - Boots to a friendly TUI wizard, no command line required
- **Choose Your Stack** - Pick from Plex, Jellyfin, or Emby as your media server
- **Complete Arr Suite** - Radarr, Sonarr, Lidarr, Readarr, and Prowlarr pre-configured
- **Flexible Downloads** - Support for both torrents (qBittorrent) and Usenet (SABnzbd/NZBGet)
- **Modern Dashboard** - Homepage or Heimdall for easy service access
- **Auto-Updates** - Watchtower keeps all containers current
- **Disposable OS** - All data lives in Docker volumes; reinstall without losing config

## Quick Start

### Option 1: Download the ISO (Recommended)

1. Download the latest release from [Releases](../../releases)
2. Flash to USB with [Balena Etcher](https://etcher.io) or `dd`
3. Boot target machine from USB
4. Follow the on-screen wizard

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/UpstateNate/AstroMediaServer.git
cd AstroMediaServer

# Install build dependencies (Ubuntu/Debian)
sudo apt install xorriso p7zip-full wget genisoimage

# Build the ISO
./scripts/build-iso.sh

# Output: output/astro-media-server-v0.1.iso
```

### Option 3: Run Setup on Existing Ubuntu/Debian Server

```bash
# Install prerequisites
sudo apt update
sudo apt install docker.io docker-compose-v2 python3 python3-yaml whiptail git

# Enable and start Docker
sudo systemctl enable --now docker

# Add your user to the docker group (logout/login required)
sudo usermod -aG docker $USER

# Clone the repository
git clone https://github.com/UpstateNate/AstroMediaServer.git
cd AstroMediaServer

# Run the setup wizard
sudo python3 scripts/astro-setup.py
```

## Default Credentials

| Field | Value |
|-------|-------|
| Username | `astro-admin` |
| Password | `astro` |

**Change the password immediately after first login:**
```bash
passwd
```

## Application Stack

| Category | Options | Default Ports |
|----------|---------|---------------|
| **Media Server** | Plex / Jellyfin / Emby | 32400 / 8096 |
| **Movies** | Radarr | 7878 |
| **TV Shows** | Sonarr | 8989 |
| **Music** | Lidarr | 8686 |
| **Books** | Readarr | 8787 |
| **Indexers** | Prowlarr | 9696 |
| **Torrents** | qBittorrent | 8080 |
| **Usenet** | SABnzbd / NZBGet | 8080 / 6789 |
| **Gateway** | Traefik / Nginx Proxy Manager | 80, 443 |
| **Dashboard** | Homepage / Heimdall | 3000 |

## Directory Structure

```
/opt/astro/
├── config/           # Container configurations
│   ├── jellyfin/
│   ├── radarr/
│   ├── sonarr/
│   └── ...
├── media/            # Media libraries
│   ├── movies/
│   ├── tv/
│   ├── music/
│   └── books/
├── torrents/         # Torrent downloads
├── usenet/           # Usenet downloads
└── docker-compose.yml
```

## Managing Services

```bash
cd /opt/astro

# View running containers
docker compose ps

# Restart all services
docker compose restart

# Stop all services
docker compose down

# Start all services
docker compose up -d

# View logs
docker compose logs -f [service_name]

# Update all containers
docker compose pull && docker compose up -d
```

## Requirements

### Hardware
- **CPU:** x86_64 processor (Intel/AMD)
- **RAM:** 4GB minimum, 8GB+ recommended
- **Storage:** 32GB for OS, additional drives for media
- **Network:** Ethernet recommended

### Software (for building)
- Ubuntu/Debian host (or WSL2)
- `xorriso`, `p7zip-full`, `genisoimage`

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - **Start here!** Connect all your services
- [Project Charter](docs/CHARTER.md) - Full technical specification
- [Contributing](CONTRIBUTING.md) - How to contribute

## Roadmap

- [x] Phase 1: Autoinstall ISO configuration
- [x] Phase 2: TUI wizard and Docker Compose generator
- [x] Phase 3: systemd integration
- [x] Phase 4: Branding and polish
- [ ] Hardware transcoding support (NVIDIA/Intel QSV)
- [ ] VPN integration for downloaders
- [ ] Backup/restore functionality
- [ ] Web-based post-install configuration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LinuxServer.io](https://linuxserver.io) - Docker images
- [Servarr](https://wiki.servarr.com) - The *Arr suite
- Ubuntu - Base operating system

---

<p align="center">
  <sub>Built with caffeine and mass media addiction</sub>
</p>
