#!/usr/bin/env python3
"""
AstroMediaServer Setup Wizard
A whiptail-based TUI for configuring the media server stack.
"""

import subprocess
import os
import sys
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# Configuration paths
ASTRO_DIR = Path("/opt/astro")
CONFIG_DIR = ASTRO_DIR / "config"
MEDIA_DIR = ASTRO_DIR / "media"
COMPOSE_FILE = ASTRO_DIR / "docker-compose.yml"

# Default environment variables
DEFAULT_PUID = "1000"
DEFAULT_PGID = "1000"
DEFAULT_TZ = "America/New_York"


@dataclass
class UserConfig:
    """Stores user selections from the wizard."""

    media_server: str = "jellyfin"
    downloader: str = "qbittorrent"
    gateway: str = "traefik"
    dashboard: str = "homepage"
    timezone: str = DEFAULT_TZ
    puid: str = DEFAULT_PUID
    pgid: str = DEFAULT_PGID
    enable_usenet: bool = False
    enable_torrents: bool = True
    # New features
    enable_vpn: bool = False
    vpn_provider: str = ""
    vpn_username: str = ""
    vpn_password: str = ""
    extra_services: list = None  # Bazarr, Overseerr, Tautulli, Portainer
    enable_transcoding: bool = False
    transcoding_type: str = ""  # nvidia, intel, none

    def __post_init__(self):
        if self.extra_services is None:
            self.extra_services = []


class WhiptailUI:
    """Wrapper for whiptail dialog boxes."""

    TITLE = "AstroMediaServer Setup"
    BACKTITLE = "AstroMediaServer v0.1 - Home Media Empire"

    @staticmethod
    def _run(args: list, input_text: str = None) -> tuple[int, str]:
        """Run whiptail command and return (returncode, output)."""
        cmd = ["whiptail", "--title", WhiptailUI.TITLE, "--backtitle", WhiptailUI.BACKTITLE] + args
        try:
            result = subprocess.run(
                cmd,
                input=input_text.encode() if input_text else None,
                capture_output=True,
                text=False,
            )
            # whiptail outputs to stderr
            return result.returncode, result.stderr.decode().strip()
        except FileNotFoundError:
            print("Error: whiptail not found. Please install it.")
            sys.exit(1)

    @staticmethod
    def msgbox(text: str, height: int = 10, width: int = 60) -> None:
        """Display a message box."""
        WhiptailUI._run(["--msgbox", text, str(height), str(width)])

    @staticmethod
    def yesno(text: str, height: int = 10, width: int = 60) -> bool:
        """Display a yes/no dialog. Returns True for yes."""
        code, _ = WhiptailUI._run(["--yesno", text, str(height), str(width)])
        return code == 0

    @staticmethod
    def menu(text: str, choices: list[tuple[str, str]], height: int = 20, width: int = 70, menu_height: int = 10) -> Optional[str]:
        """Display a menu and return the selected item."""
        args = ["--menu", text, str(height), str(width), str(menu_height)]
        for tag, description in choices:
            args.extend([tag, description])
        code, output = WhiptailUI._run(args)
        return output if code == 0 else None

    @staticmethod
    def checklist(text: str, choices: list[tuple[str, str, str]], height: int = 20, width: int = 70, list_height: int = 10) -> list[str]:
        """Display a checklist and return selected items."""
        args = ["--checklist", text, str(height), str(width), str(list_height)]
        for tag, description, status in choices:
            args.extend([tag, description, status])
        code, output = WhiptailUI._run(args)
        if code != 0:
            return []
        # Parse output - items are quoted and space-separated
        return [item.strip('"') for item in output.split('" "') if item.strip('"')]

    @staticmethod
    def inputbox(text: str, default: str = "", height: int = 10, width: int = 60) -> Optional[str]:
        """Display an input box and return the entered text."""
        code, output = WhiptailUI._run(["--inputbox", text, str(height), str(width), default])
        return output if code == 0 else None

    @staticmethod
    def gauge(text: str, percent: int, height: int = 7, width: int = 60) -> None:
        """Display a progress gauge."""
        WhiptailUI._run(["--gauge", text, str(height), str(width), str(percent)])


class ComposeGenerator:
    """Generates docker-compose.yml based on user configuration."""

    # LinuxServer.io images
    IMAGES = {
        # Media Servers
        "plex": "lscr.io/linuxserver/plex:latest",
        "jellyfin": "lscr.io/linuxserver/jellyfin:latest",
        "emby": "lscr.io/linuxserver/emby:latest",
        # Arr Suite
        "radarr": "lscr.io/linuxserver/radarr:latest",
        "sonarr": "lscr.io/linuxserver/sonarr:latest",
        "lidarr": "lscr.io/linuxserver/lidarr:latest",
        "readarr": "lscr.io/linuxserver/readarr:latest",
        "prowlarr": "lscr.io/linuxserver/prowlarr:latest",
        "bazarr": "lscr.io/linuxserver/bazarr:latest",
        # Downloaders
        "qbittorrent": "lscr.io/linuxserver/qbittorrent:latest",
        "sabnzbd": "lscr.io/linuxserver/sabnzbd:latest",
        "nzbget": "lscr.io/linuxserver/nzbget:latest",
        # Gateway
        "traefik": "traefik:latest",
        "nginx-proxy-manager": "jc21/nginx-proxy-manager:latest",
        # Dashboard
        "homepage": "ghcr.io/gethomepage/homepage:latest",
        "heimdall": "lscr.io/linuxserver/heimdall:latest",
        # Utilities
        "watchtower": "containrrr/watchtower:latest",
        "portainer": "portainer/portainer-ce:latest",
        # Extras
        "overseerr": "lscr.io/linuxserver/overseerr:latest",
        "tautulli": "lscr.io/linuxserver/tautulli:latest",
        # VPN
        "gluetun": "qmcgaw/gluetun:latest",
    }

    def __init__(self, config: UserConfig):
        self.config = config
        self.services = {}

    def _base_env(self) -> dict:
        """Return base environment variables."""
        return {
            "PUID": self.config.puid,
            "PGID": self.config.pgid,
            "TZ": self.config.timezone,
        }

    def _add_media_server(self) -> None:
        """Add selected media server to compose."""
        server = self.config.media_server

        base = {
            "image": self.IMAGES[server],
            "container_name": server,
            "restart": "unless-stopped",
            "environment": self._base_env(),
            "volumes": [
                f"{CONFIG_DIR}/{server}:/config",
                f"{MEDIA_DIR}/movies:/movies",
                f"{MEDIA_DIR}/tv:/tv",
                f"{MEDIA_DIR}/music:/music",
            ],
        }

        if server == "plex":
            base["network_mode"] = "host"
            base["environment"]["VERSION"] = "docker"
        elif server == "jellyfin":
            base["ports"] = ["8096:8096"]
        elif server == "emby":
            base["ports"] = ["8096:8096"]

        self.services[server] = base

    def _add_arr_suite(self) -> None:
        """Add Radarr, Sonarr, Lidarr, Readarr, Prowlarr."""
        arr_configs = {
            "radarr": {"port": "7878:7878"},
            "sonarr": {"port": "8989:8989"},
            "lidarr": {"port": "8686:8686"},
            "readarr": {"port": "8787:8787"},
            "prowlarr": {"port": "9696:9696"},
        }

        for name, conf in arr_configs.items():
            volumes = [f"{CONFIG_DIR}/{name}:/config"]

            # Add media volumes for content managers
            if name in ["radarr", "sonarr", "lidarr", "readarr"]:
                volumes.extend([
                    f"{MEDIA_DIR}/movies:/movies",
                    f"{MEDIA_DIR}/tv:/tv",
                    f"{MEDIA_DIR}/music:/music",
                    f"{MEDIA_DIR}/books:/books",
                ])
                if self.config.enable_torrents:
                    volumes.append(f"{ASTRO_DIR}/torrents:/downloads/torrents")
                if self.config.enable_usenet:
                    volumes.append(f"{ASTRO_DIR}/usenet:/downloads/usenet")

            self.services[name] = {
                "image": self.IMAGES[name],
                "container_name": name,
                "restart": "unless-stopped",
                "environment": self._base_env(),
                "ports": [conf["port"]],
                "volumes": volumes,
            }

    def _add_downloader(self) -> None:
        """Add selected downloader(s)."""
        if self.config.enable_torrents:
            downloader = self.config.downloader if self.config.downloader != "sabnzbd" else "qbittorrent"
            self.services["qbittorrent"] = {
                "image": self.IMAGES["qbittorrent"],
                "container_name": "qbittorrent",
                "restart": "unless-stopped",
                "environment": {
                    **self._base_env(),
                    "WEBUI_PORT": "8080",
                },
                "ports": ["8080:8080", "6881:6881", "6881:6881/udp"],
                "volumes": [
                    f"{CONFIG_DIR}/qbittorrent:/config",
                    f"{ASTRO_DIR}/torrents:/downloads",
                ],
            }

        if self.config.enable_usenet:
            usenet_client = self.config.downloader if self.config.downloader in ["sabnzbd", "nzbget"] else "sabnzbd"
            port = "8080" if usenet_client == "sabnzbd" else "6789"

            self.services[usenet_client] = {
                "image": self.IMAGES[usenet_client],
                "container_name": usenet_client,
                "restart": "unless-stopped",
                "environment": self._base_env(),
                "ports": [f"{port}:{port}"],
                "volumes": [
                    f"{CONFIG_DIR}/{usenet_client}:/config",
                    f"{ASTRO_DIR}/usenet:/downloads",
                ],
            }

    def _add_gateway(self) -> None:
        """Add reverse proxy/gateway."""
        gateway = self.config.gateway

        if gateway == "traefik":
            self.services["traefik"] = {
                "image": self.IMAGES["traefik"],
                "container_name": "traefik",
                "restart": "unless-stopped",
                "command": [
                    "--api.dashboard=true",
                    "--api.insecure=true",
                    "--providers.docker=true",
                    "--providers.docker.exposedbydefault=false",
                    "--entrypoints.web.address=:80",
                ],
                "ports": ["80:80", "8081:8080"],
                "volumes": [
                    "/var/run/docker.sock:/var/run/docker.sock:ro",
                    f"{CONFIG_DIR}/traefik:/etc/traefik",
                ],
            }
        elif gateway == "nginx-proxy-manager":
            self.services["nginx-proxy-manager"] = {
                "image": self.IMAGES["nginx-proxy-manager"],
                "container_name": "nginx-proxy-manager",
                "restart": "unless-stopped",
                "ports": ["80:80", "443:443", "81:81"],
                "volumes": [
                    f"{CONFIG_DIR}/npm/data:/data",
                    f"{CONFIG_DIR}/npm/letsencrypt:/etc/letsencrypt",
                ],
            }

    def _add_dashboard(self) -> None:
        """Add dashboard application."""
        dashboard = self.config.dashboard

        if dashboard == "homepage":
            self.services["homepage"] = {
                "image": self.IMAGES["homepage"],
                "container_name": "homepage",
                "restart": "unless-stopped",
                "ports": ["3000:3000"],
                "volumes": [
                    f"{CONFIG_DIR}/homepage:/app/config",
                    "/var/run/docker.sock:/var/run/docker.sock:ro",
                ],
                "environment": self._base_env(),
            }
        elif dashboard == "heimdall":
            self.services["heimdall"] = {
                "image": self.IMAGES["heimdall"],
                "container_name": "heimdall",
                "restart": "unless-stopped",
                "ports": ["3000:80"],
                "volumes": [f"{CONFIG_DIR}/heimdall:/config"],
                "environment": self._base_env(),
            }

    def _add_watchtower(self) -> None:
        """Add Watchtower for automatic updates."""
        self.services["watchtower"] = {
            "image": self.IMAGES["watchtower"],
            "container_name": "watchtower",
            "restart": "unless-stopped",
            "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
            "environment": {
                "WATCHTOWER_CLEANUP": "true",
                "WATCHTOWER_SCHEDULE": "0 0 4 * * *",  # 4 AM daily
            },
        }

    def _add_extra_services(self) -> None:
        """Add optional extra services (Bazarr, Overseerr, Tautulli, Portainer)."""
        if "bazarr" in self.config.extra_services:
            self.services["bazarr"] = {
                "image": self.IMAGES["bazarr"],
                "container_name": "bazarr",
                "restart": "unless-stopped",
                "environment": self._base_env(),
                "ports": ["6767:6767"],
                "volumes": [
                    f"{CONFIG_DIR}/bazarr:/config",
                    f"{MEDIA_DIR}/movies:/movies",
                    f"{MEDIA_DIR}/tv:/tv",
                ],
            }

        if "overseerr" in self.config.extra_services:
            self.services["overseerr"] = {
                "image": self.IMAGES["overseerr"],
                "container_name": "overseerr",
                "restart": "unless-stopped",
                "environment": self._base_env(),
                "ports": ["5055:5055"],
                "volumes": [f"{CONFIG_DIR}/overseerr:/config"],
            }

        if "tautulli" in self.config.extra_services:
            self.services["tautulli"] = {
                "image": self.IMAGES["tautulli"],
                "container_name": "tautulli",
                "restart": "unless-stopped",
                "environment": self._base_env(),
                "ports": ["8181:8181"],
                "volumes": [f"{CONFIG_DIR}/tautulli:/config"],
            }

        if "portainer" in self.config.extra_services:
            self.services["portainer"] = {
                "image": self.IMAGES["portainer"],
                "container_name": "portainer",
                "restart": "unless-stopped",
                "ports": ["9000:9000"],
                "volumes": [
                    "/var/run/docker.sock:/var/run/docker.sock",
                    f"{CONFIG_DIR}/portainer:/data",
                ],
            }

    def _add_vpn(self) -> None:
        """Add VPN container (gluetun) for download clients."""
        if not self.config.enable_vpn:
            return

        self.services["gluetun"] = {
            "image": self.IMAGES["gluetun"],
            "container_name": "gluetun",
            "restart": "unless-stopped",
            "cap_add": ["NET_ADMIN"],
            "devices": ["/dev/net/tun:/dev/net/tun"],
            "environment": {
                "VPN_SERVICE_PROVIDER": self.config.vpn_provider,
                "VPN_TYPE": "openvpn",
                "OPENVPN_USER": self.config.vpn_username,
                "OPENVPN_PASSWORD": self.config.vpn_password,
                "TZ": self.config.timezone,
            },
            "ports": [
                "8080:8080",      # qBittorrent WebUI
                "6881:6881",      # qBittorrent
                "6881:6881/udp",
            ],
            "volumes": [f"{CONFIG_DIR}/gluetun:/gluetun"],
        }

        # Modify qbittorrent to use VPN network
        if "qbittorrent" in self.services:
            # Remove ports from qbittorrent (handled by gluetun)
            self.services["qbittorrent"].pop("ports", None)
            self.services["qbittorrent"]["network_mode"] = "service:gluetun"
            self.services["qbittorrent"]["depends_on"] = ["gluetun"]

    def _configure_transcoding(self) -> None:
        """Configure hardware transcoding for media server."""
        if not self.config.enable_transcoding:
            return

        server = self.config.media_server
        if server not in self.services:
            return

        if self.config.transcoding_type == "nvidia":
            # Add NVIDIA GPU support
            self.services[server]["runtime"] = "nvidia"
            self.services[server]["environment"]["NVIDIA_VISIBLE_DEVICES"] = "all"
            if server == "jellyfin":
                self.services[server]["environment"]["NVIDIA_DRIVER_CAPABILITIES"] = "all"
        elif self.config.transcoding_type == "intel":
            # Add Intel QuickSync support (vaapi)
            if "devices" not in self.services[server]:
                self.services[server]["devices"] = []
            self.services[server]["devices"].append("/dev/dri:/dev/dri")

    def generate(self) -> dict:
        """Generate the complete docker-compose configuration."""
        self._add_media_server()
        self._add_arr_suite()
        self._add_downloader()
        self._add_gateway()
        self._add_dashboard()
        self._add_watchtower()
        self._add_extra_services()
        self._add_vpn()
        self._configure_transcoding()

        return {
            "version": "3.8",
            "services": self.services,
            "networks": {
                "default": {
                    "name": "astro-network",
                }
            },
        }

    def generate_homepage_config(self) -> None:
        """Generate Homepage dashboard configuration files."""
        if self.config.dashboard != "homepage":
            return

        homepage_dir = CONFIG_DIR / "homepage"
        homepage_dir.mkdir(parents=True, exist_ok=True)

        # Generate services.yaml
        services = self._build_homepage_services()
        with open(homepage_dir / "services.yaml", "w") as f:
            yaml.dump(services, f, default_flow_style=False, sort_keys=False)

        # Generate settings.yaml
        settings = {
            "title": "AstroMediaServer",
            "theme": "dark",
            "color": "slate",
            "headerStyle": "boxed",
            "layout": {
                "Media": {"style": "row", "columns": 3},
                "Downloads": {"style": "row", "columns": 2},
                "Management": {"style": "row", "columns": 4},
                "System": {"style": "row", "columns": 2},
            },
        }
        with open(homepage_dir / "settings.yaml", "w") as f:
            yaml.dump(settings, f, default_flow_style=False, sort_keys=False)

        # Generate widgets.yaml
        widgets = [
            {"resources": {"cpu": True, "memory": True, "disk": "/"}},
            {"datetime": {"text_size": "xl", "format": {"dateStyle": "long", "timeStyle": "short"}}},
        ]
        with open(homepage_dir / "widgets.yaml", "w") as f:
            yaml.dump(widgets, f, default_flow_style=False, sort_keys=False)

        # Generate docker.yaml for container integration
        docker_config = {"my-docker": {"socket": "/var/run/docker.sock"}}
        with open(homepage_dir / "docker.yaml", "w") as f:
            yaml.dump(docker_config, f, default_flow_style=False, sort_keys=False)

    def _build_homepage_services(self) -> list:
        """Build Homepage services configuration."""
        services = []

        # Media section
        media_services = []
        server = self.config.media_server
        port = {"jellyfin": 8096, "plex": 32400, "emby": 8096}.get(server, 8096)
        media_services.append({
            server.title(): {
                "icon": f"{server}.png",
                "href": f"http://{{{{HOMEPAGE_VAR_SERVER_IP}}}}:{port}",
                "description": "Media Server",
                "container": server,
                "server": "my-docker",
            }
        })

        if "overseerr" in self.config.extra_services:
            media_services.append({
                "Overseerr": {
                    "icon": "overseerr.png",
                    "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:5055",
                    "description": "Media Requests",
                    "container": "overseerr",
                    "server": "my-docker",
                }
            })

        if "tautulli" in self.config.extra_services:
            media_services.append({
                "Tautulli": {
                    "icon": "tautulli.png",
                    "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:8181",
                    "description": "Plex Statistics",
                    "container": "tautulli",
                    "server": "my-docker",
                }
            })

        services.append({"Media": media_services})

        # Downloads section
        download_services = []
        if self.config.enable_torrents:
            download_services.append({
                "qBittorrent": {
                    "icon": "qbittorrent.png",
                    "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:8080",
                    "description": "Torrent Client",
                    "container": "qbittorrent",
                    "server": "my-docker",
                }
            })
        if self.config.enable_usenet:
            client = "sabnzbd" if self.config.downloader == "sabnzbd" else "nzbget"
            port = 8080 if client == "sabnzbd" else 6789
            download_services.append({
                client.title(): {
                    "icon": f"{client}.png",
                    "href": f"http://{{{{HOMEPAGE_VAR_SERVER_IP}}}}:{port}",
                    "description": "Usenet Client",
                    "container": client,
                    "server": "my-docker",
                }
            })

        if download_services:
            services.append({"Downloads": download_services})

        # Management section (Arr suite)
        management_services = [
            {"Radarr": {"icon": "radarr.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:7878", "description": "Movies", "container": "radarr", "server": "my-docker"}},
            {"Sonarr": {"icon": "sonarr.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:8989", "description": "TV Shows", "container": "sonarr", "server": "my-docker"}},
            {"Lidarr": {"icon": "lidarr.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:8686", "description": "Music", "container": "lidarr", "server": "my-docker"}},
            {"Readarr": {"icon": "readarr.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:8787", "description": "Books", "container": "readarr", "server": "my-docker"}},
            {"Prowlarr": {"icon": "prowlarr.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:9696", "description": "Indexers", "container": "prowlarr", "server": "my-docker"}},
        ]

        if "bazarr" in self.config.extra_services:
            management_services.append({
                "Bazarr": {"icon": "bazarr.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:6767", "description": "Subtitles", "container": "bazarr", "server": "my-docker"}
            })

        services.append({"Management": management_services})

        # System section
        system_services = []
        if "portainer" in self.config.extra_services:
            system_services.append({
                "Portainer": {"icon": "portainer.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:9000", "description": "Container Management", "container": "portainer", "server": "my-docker"}
            })

        gateway = self.config.gateway
        if gateway == "traefik":
            system_services.append({
                "Traefik": {"icon": "traefik.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:8081", "description": "Reverse Proxy", "container": "traefik", "server": "my-docker"}
            })
        elif gateway == "nginx-proxy-manager":
            system_services.append({
                "NPM": {"icon": "nginx-proxy-manager.png", "href": "http://{{HOMEPAGE_VAR_SERVER_IP}}:81", "description": "Reverse Proxy", "container": "nginx-proxy-manager", "server": "my-docker"}
            })

        if system_services:
            services.append({"System": system_services})

        return services


class SetupWizard:
    """Main setup wizard orchestrator."""

    def __init__(self):
        self.ui = WhiptailUI()
        self.config = UserConfig()

    def show_welcome(self) -> bool:
        """Display welcome message."""
        welcome_text = """
Welcome to AstroMediaServer!

This wizard will help you configure your
personal home media server stack.

The following components will be set up:
- Media Server (Plex/Jellyfin/Emby)
- The *Arr Suite (Radarr, Sonarr, etc.)
- Download clients
- Reverse proxy and dashboard

Press OK to continue or Cancel to exit.
"""
        return self.ui.yesno(welcome_text, height=18, width=55)

    def select_media_server(self) -> bool:
        """Let user choose media server."""
        choices = [
            ("jellyfin", "Free & open source media server"),
            ("plex", "Popular media server (requires account)"),
            ("emby", "Media server with plugins"),
        ]

        result = self.ui.menu(
            "Select your preferred media server:",
            choices,
            height=15,
            menu_height=5,
        )

        if result:
            self.config.media_server = result
            return True
        return False

    def select_download_method(self) -> bool:
        """Let user choose download methods."""
        choices = [
            ("torrents", "BitTorrent downloads", "ON"),
            ("usenet", "Usenet downloads (requires provider)", "OFF"),
        ]

        result = self.ui.checklist(
            "Select your download methods:\n(Space to toggle, Enter to confirm)",
            choices,
            height=15,
            list_height=4,
        )

        if result is not None:
            self.config.enable_torrents = "torrents" in result
            self.config.enable_usenet = "usenet" in result
            return True
        return False

    def select_downloader(self) -> bool:
        """Let user choose downloader application."""
        choices = [("qbittorrent", "Popular torrent client with web UI")]

        if self.config.enable_usenet:
            choices.extend([
                ("sabnzbd", "Python-based Usenet downloader"),
                ("nzbget", "Efficient C++ Usenet downloader"),
            ])

        if len(choices) == 1:
            self.config.downloader = "qbittorrent"
            return True

        result = self.ui.menu(
            "Select your preferred downloader:",
            choices,
            height=15,
            menu_height=5,
        )

        if result:
            self.config.downloader = result
            return True
        return False

    def select_gateway(self) -> bool:
        """Let user choose reverse proxy."""
        choices = [
            ("traefik", "Modern reverse proxy with auto-discovery"),
            ("nginx-proxy-manager", "Easy-to-use GUI-based proxy"),
        ]

        result = self.ui.menu(
            "Select your reverse proxy/gateway:",
            choices,
            height=14,
            menu_height=4,
        )

        if result:
            self.config.gateway = result
            return True
        return False

    def select_dashboard(self) -> bool:
        """Let user choose dashboard."""
        choices = [
            ("homepage", "Modern dashboard with service widgets"),
            ("heimdall", "Simple application launcher"),
        ]

        result = self.ui.menu(
            "Select your dashboard application:",
            choices,
            height=14,
            menu_height=4,
        )

        if result:
            self.config.dashboard = result
            return True
        return False

    def configure_timezone(self) -> bool:
        """Let user set timezone."""
        result = self.ui.inputbox(
            "Enter your timezone (e.g., America/New_York):",
            default=DEFAULT_TZ,
        )

        if result:
            self.config.timezone = result
            return True
        return False

    def select_extra_services(self) -> bool:
        """Let user choose additional services."""
        choices = [
            ("bazarr", "Automatic subtitle downloads", "ON"),
            ("overseerr", "Media request management", "OFF"),
            ("tautulli", "Plex/media statistics", "OFF"),
            ("portainer", "Docker container management", "ON"),
        ]

        result = self.ui.checklist(
            "Select additional services:\n(Space to toggle, Enter to confirm)",
            choices,
            height=16,
            list_height=6,
        )

        if result is not None:
            self.config.extra_services = result
            return True
        return False

    def configure_vpn(self) -> bool:
        """Configure VPN for download clients."""
        if not self.config.enable_torrents:
            return True

        if not self.ui.yesno(
            "Would you like to route download traffic\nthrough a VPN for privacy?\n\n"
            "This requires a VPN subscription\n(NordVPN, ExpressVPN, PIA, etc.)",
            height=12,
        ):
            self.config.enable_vpn = False
            return True

        self.config.enable_vpn = True

        # Select VPN provider
        providers = [
            ("nordvpn", "NordVPN"),
            ("expressvpn", "ExpressVPN"),
            ("private internet access", "Private Internet Access (PIA)"),
            ("surfshark", "Surfshark"),
            ("mullvad", "Mullvad"),
            ("protonvpn", "ProtonVPN"),
            ("windscribe", "Windscribe"),
            ("custom", "Other OpenVPN provider"),
        ]

        provider = self.ui.menu(
            "Select your VPN provider:",
            providers,
            height=18,
            menu_height=10,
        )

        if not provider:
            self.config.enable_vpn = False
            return True

        self.config.vpn_provider = provider

        # Get credentials
        username = self.ui.inputbox("Enter VPN username/email:")
        if not username:
            self.config.enable_vpn = False
            return True
        self.config.vpn_username = username

        password = self.ui.inputbox("Enter VPN password:")
        if not password:
            self.config.enable_vpn = False
            return True
        self.config.vpn_password = password

        return True

    def detect_hardware_transcoding(self) -> bool:
        """Detect and configure hardware transcoding."""
        # Check for NVIDIA GPU
        nvidia_available = os.path.exists("/dev/nvidia0") or self._check_nvidia()
        # Check for Intel iGPU (vaapi)
        intel_available = os.path.exists("/dev/dri/renderD128")

        if not nvidia_available and not intel_available:
            self.ui.msgbox(
                "No compatible GPU detected for\nhardware transcoding.\n\n"
                "Software transcoding will be used.\n\n"
                "Supported: NVIDIA GPUs, Intel QuickSync",
                height=12,
            )
            return True

        options = []
        if nvidia_available:
            options.append(("nvidia", "NVIDIA GPU (NVENC)"))
        if intel_available:
            options.append(("intel", "Intel QuickSync (VAAPI)"))
        options.append(("none", "Use software transcoding"))

        if len(options) == 1:
            choice = options[0][0]
        else:
            choice = self.ui.menu(
                "Hardware transcoding detected!\nSelect acceleration method:",
                options,
                height=14,
                menu_height=5,
            )

        if choice and choice != "none":
            self.config.enable_transcoding = True
            self.config.transcoding_type = choice
        else:
            self.config.enable_transcoding = False

        return True

    def _check_nvidia(self) -> bool:
        """Check if NVIDIA drivers are available."""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def show_summary(self) -> bool:
        """Display configuration summary."""
        extras = ", ".join(self.config.extra_services) if self.config.extra_services else "None"
        vpn_status = f"Enabled ({self.config.vpn_provider})" if self.config.enable_vpn else "Disabled"
        transcode = self.config.transcoding_type.upper() if self.config.enable_transcoding else "Software"

        summary = f"""
Configuration Summary:

Media Server:  {self.config.media_server.title()}
Gateway:       {self.config.gateway.replace('-', ' ').title()}
Dashboard:     {self.config.dashboard.title()}

Download Methods:
  Torrents:    {'Enabled' if self.config.enable_torrents else 'Disabled'}
  Usenet:      {'Enabled' if self.config.enable_usenet else 'Disabled'}
  VPN:         {vpn_status}

Hardware Transcoding: {transcode}

Extra Services: {extras}

Timezone:      {self.config.timezone}

Always Included:
  Radarr, Sonarr, Lidarr, Readarr,
  Prowlarr, Watchtower

Proceed with this configuration?
"""
        return self.ui.yesno(summary, height=28, width=55)

    def create_directories(self) -> None:
        """Create required directory structure."""
        dirs = [
            CONFIG_DIR,
            MEDIA_DIR / "movies",
            MEDIA_DIR / "tv",
            MEDIA_DIR / "music",
            MEDIA_DIR / "books",
            ASTRO_DIR / "torrents",
            ASTRO_DIR / "usenet",
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            os.chown(d, int(self.config.puid), int(self.config.pgid))

    def generate_compose(self) -> None:
        """Generate docker-compose.yml file."""
        self.generator = ComposeGenerator(self.config)
        compose_config = self.generator.generate()

        with open(COMPOSE_FILE, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)

    def generate_homepage_config(self) -> None:
        """Generate Homepage dashboard configuration."""
        if hasattr(self, 'generator'):
            self.generator.generate_homepage_config()

    def deploy_stack(self) -> bool:
        """Deploy the Docker stack."""
        self.ui.msgbox("Deploying services...\n\nThis may take several minutes as container images are downloaded.", height=10)

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"],
                cwd=str(ASTRO_DIR),
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception as e:
            self.ui.msgbox(f"Deployment failed:\n{str(e)}", height=10)
            return False

    def show_completion(self) -> None:
        """Display completion message with access URLs."""
        # Get IP address
        try:
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True,
                text=True,
            )
            ip = result.stdout.strip().split()[0]
        except Exception:
            ip = "YOUR_IP"

        ports = {
            "jellyfin": 8096,
            "plex": 32400,
            "emby": 8096,
            "radarr": 7878,
            "sonarr": 8989,
            "prowlarr": 9696,
            "homepage": 3000,
            "heimdall": 3000,
            "qbittorrent": 8080,
        }

        media_port = ports.get(self.config.media_server, 8096)
        dashboard_port = ports.get(self.config.dashboard, 3000)

        completion_text = f"""
Setup Complete!

Your services are now running.

Access your server at:

Dashboard:     http://{ip}:{dashboard_port}
{self.config.media_server.title()}:      http://{ip}:{media_port}
Radarr:        http://{ip}:7878
Sonarr:        http://{ip}:8989
Prowlarr:      http://{ip}:9696

Configuration saved to:
{COMPOSE_FILE}

To manage services:
  cd {ASTRO_DIR}
  docker compose [up|down|restart]

Enjoy your media server!
"""
        self.ui.msgbox(completion_text, height=26, width=55)

    def run(self) -> int:
        """Run the setup wizard."""
        steps = [
            self.show_welcome,
            self.select_media_server,
            self.select_download_method,
            self.select_downloader,
            self.select_gateway,
            self.select_dashboard,
            self.select_extra_services,
            self.configure_vpn,
            self.detect_hardware_transcoding,
            self.configure_timezone,
            self.show_summary,
        ]

        for step in steps:
            if not step():
                self.ui.msgbox("Setup cancelled.")
                return 1

        # Execute setup
        try:
            self.create_directories()
            self.generate_compose()
            self.generate_homepage_config()

            if self.deploy_stack():
                self.show_completion()
                return 0
            else:
                self.ui.msgbox("Deployment encountered errors.\nCheck docker logs for details.")
                return 1
        except Exception as e:
            self.ui.msgbox(f"Setup failed:\n{str(e)}")
            return 1


def main():
    """Entry point."""
    # Ensure running as root for system changes
    if os.geteuid() != 0:
        print("This script must be run as root")
        print("Try: sudo python3 astro-setup.py")
        sys.exit(1)

    wizard = SetupWizard()
    sys.exit(wizard.run())


if __name__ == "__main__":
    main()
