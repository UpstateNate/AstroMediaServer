# AstroMediaServer Setup Guide

After installation, follow these steps to connect all your services together.

## Overview

```
┌─────────────┐     ┌─────────────────────────────┐
│  Prowlarr   │────▶│  Radarr / Sonarr / Lidarr   │
│ (Indexers)  │     │    (Media Management)       │
└─────────────┘     └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │   SABnzbd / qBittorrent     │
                    │    (Download Clients)       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      /opt/astro/media       │
                    │   (Movies, TV, Music)       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │           Plex              │
                    │      (Media Server)         │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │        Overseerr            │
                    │    (Request Management)     │
                    └─────────────────────────────┘
```

## Directory Structure

All services use these shared paths:

| Path | Purpose |
|------|---------|
| `/opt/astro/media/movies` | Movie library |
| `/opt/astro/media/tv` | TV show library |
| `/opt/astro/media/music` | Music library |
| `/opt/astro/usenet` | Usenet downloads |
| `/opt/astro/torrents` | Torrent downloads |
| `/opt/astro/config` | All app configurations |

---

## Step 1: Configure SABnzbd (Usenet)

**URL:** http://YOUR_IP:8080

### Initial Setup Wizard
1. Set your preferred language
2. Add your Usenet provider (you need a paid Usenet account like Newshosting, Eweka, etc.)
   - Server: Your provider's server address
   - Port: Usually 563 (SSL) or 119
   - Username/Password: From your provider
   - SSL: Enable if using port 563

### Configure Categories
Go to **Config → Categories** and add:

| Category | Folder |
|----------|--------|
| movies | `movies` |
| tv | `tv` |
| music | `music` |

### Get API Key
Go to **Config → General → Security** and copy the **API Key** (you'll need this later).

---

## Step 2: Configure Prowlarr (Indexers)

**URL:** http://YOUR_IP:9696

### Set Up Authentication
1. On first visit, set a username and password
2. Choose "Forms" authentication

### Add Indexers
1. Go to **Indexers → Add Indexer**
2. Search for your indexer (e.g., NZBgeek, DrunkenSlug, etc.)
3. Enter your API key or credentials for each indexer
4. Test and Save

### Connect to *Arr Apps
1. Go to **Settings → Apps**
2. Click **+** to add each app:

**Add Radarr:**
- Name: `Radarr`
- Sync Level: `Full Sync`
- Prowlarr Server: `http://prowlarr:9696`
- Radarr Server: `http://radarr:7878`
- API Key: (get from Radarr → Settings → General)

**Add Sonarr:**
- Name: `Sonarr`
- Sync Level: `Full Sync`
- Prowlarr Server: `http://prowlarr:9696`
- Sonarr Server: `http://sonarr:8989`
- API Key: (get from Sonarr → Settings → General)

**Add Lidarr:**
- Name: `Lidarr`
- Sync Level: `Full Sync`
- Prowlarr Server: `http://prowlarr:9696`
- Lidarr Server: `http://lidarr:8686`
- API Key: (get from Lidarr → Settings → General)

---

## Step 3: Configure Radarr (Movies)

**URL:** http://YOUR_IP:7878

### Set Up Authentication
Settings → General → Security → Set username/password

### Add Root Folder
1. Go to **Settings → Media Management**
2. Click **Add Root Folder**
3. Enter: `/movies`

### Add Download Client
1. Go to **Settings → Download Clients**
2. Click **+** and select **SABnzbd**
3. Configure:
   - Name: `SABnzbd`
   - Host: `sabnzbd`
   - Port: `8080`
   - API Key: (from SABnzbd)
   - Category: `movies`
4. Test and Save

### Get API Key (for Prowlarr/Overseerr)
Settings → General → Copy the **API Key**

---

## Step 4: Configure Sonarr (TV Shows)

**URL:** http://YOUR_IP:8989

### Set Up Authentication
Settings → General → Security → Set username/password

### Add Root Folder
1. Go to **Settings → Media Management**
2. Click **Add Root Folder**
3. Enter: `/tv`

### Add Download Client
1. Go to **Settings → Download Clients**
2. Click **+** and select **SABnzbd**
3. Configure:
   - Name: `SABnzbd`
   - Host: `sabnzbd`
   - Port: `8080`
   - API Key: (from SABnzbd)
   - Category: `tv`
4. Test and Save

### Get API Key (for Prowlarr/Overseerr)
Settings → General → Copy the **API Key**

---

## Step 5: Configure Lidarr (Music)

**URL:** http://YOUR_IP:8686

### Set Up Authentication
Settings → General → Security → Set username/password

### Add Root Folder
1. Go to **Settings → Media Management**
2. Click **Add Root Folder**
3. Enter: `/music`

### Add Download Client
1. Go to **Settings → Download Clients**
2. Click **+** and select **SABnzbd**
3. Configure:
   - Name: `SABnzbd`
   - Host: `sabnzbd`
   - Port: `8080`
   - API Key: (from SABnzbd)
   - Category: `music`
4. Test and Save

---

## Step 6: Configure Plex

**URL:** http://YOUR_IP:32400/web

### Initial Setup
1. Sign in with your Plex account (create one at plex.tv if needed)
2. Name your server (e.g., "AstroMediaServer")
3. Skip "Get Plex Pass" if you don't want premium features

### Add Libraries
1. Go to **Settings → Manage → Libraries**
2. Add each library:

**Movies:**
- Type: Movies
- Folder: `/movies`

**TV Shows:**
- Type: TV Shows
- Folder: `/tv`

**Music:**
- Type: Music
- Folder: `/music`

### Get Plex Token (for Overseerr)
1. Open any media item in Plex web
2. Click **Get Info** (or **...** → **Get Info**)
3. Click **View XML**
4. In the URL, find `X-Plex-Token=XXXXX` - copy that token

---

## Step 7: Configure Overseerr (Requests)

**URL:** http://YOUR_IP:5055

### Initial Setup
1. Sign in with your Plex account
2. Select your Plex server from the list
3. Sync libraries (select Movies and TV Shows)

### Add Radarr
1. Go to **Settings → Services**
2. Click **Add Radarr Server**
3. Configure:
   - Default Server: Yes
   - Server Name: `Radarr`
   - Hostname: `radarr`
   - Port: `7878`
   - API Key: (from Radarr)
   - Quality Profile: Select your preferred
   - Root Folder: `/movies`
4. Test and Save

### Add Sonarr
1. Click **Add Sonarr Server**
2. Configure:
   - Default Server: Yes
   - Server Name: `Sonarr`
   - Hostname: `sonarr`
   - Port: `8989`
   - API Key: (from Sonarr)
   - Quality Profile: Select your preferred
   - Root Folder: `/tv`
4. Test and Save

---

## Quick Reference: API Keys Location

| App | Location |
|-----|----------|
| SABnzbd | Config → General → API Key |
| Radarr | Settings → General → API Key |
| Sonarr | Settings → General → API Key |
| Lidarr | Settings → General → API Key |
| Prowlarr | Settings → General → API Key |

## Quick Reference: Internal Hostnames

When connecting services to each other, use these hostnames (Docker networking):

| Service | Hostname | Port |
|---------|----------|------|
| SABnzbd | `sabnzbd` | 8080 |
| qBittorrent | `qbittorrent` | 8080 |
| Radarr | `radarr` | 7878 |
| Sonarr | `sonarr` | 8989 |
| Lidarr | `lidarr` | 8686 |
| Prowlarr | `prowlarr` | 9696 |
| Plex | `plex` | 32400 |
| Overseerr | `overseerr` | 5055 |

---

## Testing the Flow

1. **In Overseerr:** Request a movie
2. **In Radarr:** Check Activity → should show the download
3. **In SABnzbd:** Check queue → should be downloading
4. **In Radarr:** Once complete, it imports to `/movies`
5. **In Plex:** Scan library or wait for auto-scan

---

## Troubleshooting

### "Connection refused" when connecting services
- Use the Docker hostname (e.g., `radarr` not `localhost`)
- Check the container is running: `sudo docker ps`

### Downloads not importing
- Check folder permissions: `ls -la /opt/astro/media`
- Ensure Radarr/Sonarr has the same paths as download client

### Plex not seeing new files
- Manually scan: Settings → Libraries → Scan Library Files
- Check the folder path matches what you configured

### Indexers not syncing from Prowlarr
- Check Prowlarr → System → Tasks → Run "Sync Indexers"
- Verify API keys are correct
