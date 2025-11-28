# Project Charter: AstroMediaServer (AMS)

**Version:** 0.1.0 (Draft)
**Project Lead:** Nate
**Base OS:** Ubuntu Server 24.04 LTS
**Architecture:** Net-Installer / Containerized

---

## 1. Executive Summary
AstroMediaServer (AMS) is a custom Linux distribution designed to deploy a turnkey "Home Media Empire" on commodity hardware. It bridges the gap between a raw operating system and a fully configured media stack.

The system utilizes an automated "Net-Installer" approach: the base ISO installs a minimal OS, and a post-installation script fetches and configures the latest application containers (Plex/Jellyfin, Arrs, Downloaders) to ensure licensing compliance and software freshness.

## 2. Core Philosophy
* **"Drop-in & Drive":** The end user requires zero Linux CLI knowledge to reach a functional state.
* **Legal & Lean:** No proprietary binaries (Plex) are distributed in the ISO. All apps are fetched at runtime.
* **Disposable OS:** The operating system is ephemeral; all state and configuration persist in Docker volumes, making upgrades and backups trivial.
* **Personality:** The installer features "Astro" branding (space-themed ASCII art and prompts) to provide a unique, polished user experience.

---

## 3. Technical Architecture

### 3.1 Base Operating System
* **Distro:** Ubuntu Server 24.04 LTS (Noble Numbat).
* **Kernel:** Standard Linux Kernel (Generic).
* **Interface:** Headless (CLI-only).
* **Management:** SSH, Web Dashboard (Homepage/Heimdall), Portainer.

### 3.2 The Build System (ISO Generation)
We utilize **Ubuntu Autoinstall (Cloud-Init)** to modify the standard Ubuntu Server ISO.

* **Mechanism:** `user-data` injection.
* **Automated Actions:**
    * **Locale:** Enforce EN-US.
    * **Disk:** Auto-wipe and partition entire target disk (LVM).
    * **User:** Create default admin user (`astro-admin`).
    * **Packages:** Install `docker.io`, `docker-compose-v2`, `python3`, `whiptail`, `git`, `curl`.

### 3.3 Post-Installation Logic ("Astro Logic")
A systemd `oneshot` service triggers the `astro-init` script on the very first boot.

1.  **The Wizard (TUI):** A `whiptail` interface prompts the user for:
    * Media Server Preference (Plex vs. Jellyfin vs. Emby).
    * Downloader Preference (SABnzbd vs. NZBGet).
    * Network Configuration.
2.  **The Generator:** A Python script generates a `docker-compose.yml` based on user inputs.
3.  **The Deployment:**
    * Creates directory structure: `/opt/astro/{config,media,torrents,usenet}`.
    * Pulls images from Docker Hub / LSIO.
    * Launches the stack via `docker compose up -d`.

---

## 4. The Application Stack (Containers)

The following services are managed via Docker Compose:

| Category | Service Options | Function |
| :--- | :--- | :--- |
| **Gateway** | Traefik / NPM | Reverse proxy, local domain handling. |
| **Dashboard** | Homepage / Heimdall | The user's landing page. |
| **Media Server** | Plex / Jellyfin / Emby | Video streaming and transcoding. |
| **Movies** | Radarr | Movie collection manager. |
| **TV** | Sonarr | TV Series collection manager. |
| **Music** | Lidarr | Music collection manager. |
| **Books** | Readarr | E-book/Audiobook manager. |
| **Downloaders** | SABnzbd / NZBGet / QBit | Usenet and Torrent clients. |
| **Indexer** | Prowlarr | Indexer manager for the *Arrs. |
| **Maintenance** | Watchtower | Auto-updates containers. |

---

## 5. Development Roadmap

### Phase 1: The "Hello World" ISO
* **Objective:** Create a bootable ISO that performs a hands-free install of Ubuntu 24.04 and boots to a login prompt.
* **Deliverable:** Validated `user-data` YAML file.

### Phase 2: The Logic Script
* **Objective:** Develop the Python/Bash script that draws the TUI menus and generates the Docker Compose file.
* **Deliverable:** `astro-setup.py` script.

### Phase 3: Integration
* **Objective:** Inject the Phase 2 script into the Phase 1 ISO. Configure the `systemd` first-boot trigger.
* **Deliverable:** `astro-media-server-v0.1.iso`.

### Phase 4: Polish & Branding
* **Objective:** Add ASCII art, color themes, and error handling.
* **Deliverable:** Final Release Candidate.
