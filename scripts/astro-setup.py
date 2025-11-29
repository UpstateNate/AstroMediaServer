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
    request_manager: str = "none"  # overseerr, jellyseerr, ombi, none
    downloader: str = "qbittorrent"
    gateway: str = "traefik"
    dashboard: str = "homepage"
    timezone: str = DEFAULT_TZ
    puid: str = DEFAULT_PUID
    pgid: str = DEFAULT_PGID
    enable_usenet: bool = False
    enable_torrents: bool = True


class WhiptailUI:
    """Wrapper for whiptail dialog boxes."""

    TITLE = "AstroMediaServer Setup"
    BACKTITLE = "AstroMediaServer v0.1 - Home Media Empire"

    @staticmethod
    def _run(args: list, input_text: str = None) -> tuple[int, str]:
        """Run whiptail command and return (returncode, output)."""
        cmd = ["whiptail", "--title", WhiptailUI.TITLE, "--backtitle", WhiptailUI.BACKTITLE] + args
        try:
            # Whiptail needs direct terminal access for display
            # It outputs user selections to stderr
            with open("/dev/tty", "r") as tty_in, open("/dev/tty", "w") as tty_out:
                result = subprocess.run(
                    cmd,
                    stdin=tty_in,
                    stdout=tty_out,
                    stderr=subprocess.PIPE,
                )
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
        # Note: Readarr removed - LinuxServer deprecated the image (project retired)
        "prowlarr": "lscr.io/linuxserver/prowlarr:latest",
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
        # Request Managers
        "overseerr": "lscr.io/linuxserver/overseerr:latest",
        "jellyseerr": "fallenbagel/jellyseerr:latest",
        "ombi": "lscr.io/linuxserver/ombi:latest",
        # Utilities
        "watchtower": "containrrr/watchtower:latest",
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
        """Add Radarr, Sonarr, Lidarr, Prowlarr."""
        # Note: Readarr removed - LinuxServer deprecated the image
        arr_configs = {
            "radarr": {"port": "7878:7878"},
            "sonarr": {"port": "8989:8989"},
            "lidarr": {"port": "8686:8686"},
            "prowlarr": {"port": "9696:9696"},
        }

        for name, conf in arr_configs.items():
            volumes = [f"{CONFIG_DIR}/{name}:/config"]

            # Add media volumes for content managers
            if name in ["radarr", "sonarr", "lidarr"]:
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
                "environment": {
                    **self._base_env(),
                    "HOMEPAGE_ALLOWED_HOSTS": "*",  # Allow all hosts
                },
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

    def _add_request_manager(self) -> None:
        """Add request manager (Overseerr/Jellyseerr/Ombi)."""
        manager = self.config.request_manager

        if manager == "none":
            return

        if manager == "overseerr":
            self.services["overseerr"] = {
                "image": self.IMAGES["overseerr"],
                "container_name": "overseerr",
                "restart": "unless-stopped",
                "ports": ["5055:5055"],
                "volumes": [f"{CONFIG_DIR}/overseerr:/config"],
                "environment": self._base_env(),
            }
        elif manager == "jellyseerr":
            self.services["jellyseerr"] = {
                "image": self.IMAGES["jellyseerr"],
                "container_name": "jellyseerr",
                "restart": "unless-stopped",
                "ports": ["5055:5055"],
                "volumes": [f"{CONFIG_DIR}/jellyseerr:/app/config"],
                "environment": self._base_env(),
            }
        elif manager == "ombi":
            self.services["ombi"] = {
                "image": self.IMAGES["ombi"],
                "container_name": "ombi",
                "restart": "unless-stopped",
                "ports": ["3579:3579"],
                "volumes": [f"{CONFIG_DIR}/ombi:/config"],
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

    def generate(self) -> dict:
        """Generate the complete docker-compose configuration."""
        self._add_media_server()
        self._add_arr_suite()
        self._add_downloader()
        self._add_request_manager()
        self._add_gateway()
        self._add_dashboard()
        self._add_watchtower()

        return {
            "services": self.services,
            "networks": {
                "default": {
                    "name": "astro-network",
                }
            },
        }


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

    def select_request_manager(self) -> bool:
        """Let user choose request manager."""
        choices = [
            ("overseerr", "Modern request UI (best for Plex)"),
            ("jellyseerr", "Request manager for Jellyfin"),
            ("ombi", "Classic request manager (any server)"),
            ("none", "Skip - no request manager"),
        ]

        result = self.ui.menu(
            "Select a request manager:\n(Lets users request movies/shows)",
            choices,
            height=16,
            menu_height=6,
        )

        if result:
            self.config.request_manager = result
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

    def show_summary(self) -> bool:
        """Display configuration summary."""
        req_mgr = self.config.request_manager
        req_mgr_display = "None" if req_mgr == "none" else req_mgr.title()

        summary = f"""
Configuration Summary:

Media Server:     {self.config.media_server.title()}
Request Manager:  {req_mgr_display}
Gateway:          {self.config.gateway.replace('-', ' ').title()}
Dashboard:        {self.config.dashboard.title()}

Download Methods:
  Torrents:    {'Enabled' if self.config.enable_torrents else 'Disabled'}
  Usenet:      {'Enabled' if self.config.enable_usenet else 'Disabled'}

Timezone:      {self.config.timezone}

Always Included:
  Radarr, Sonarr, Lidarr,
  Prowlarr, Watchtower

Proceed with this configuration?
"""
        return self.ui.yesno(summary, height=24, width=52)

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
            # Usenet subdirectories for SABnzbd
            ASTRO_DIR / "usenet" / "complete",
            ASTRO_DIR / "usenet" / "incomplete",
            ASTRO_DIR / "usenet" / "watch",
            # Torrent subdirectories for qBittorrent
            ASTRO_DIR / "torrents" / "complete",
            ASTRO_DIR / "torrents" / "incomplete",
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            os.chown(d, int(self.config.puid), int(self.config.pgid))

    def generate_compose(self) -> None:
        """Generate docker-compose.yml file."""
        generator = ComposeGenerator(self.config)
        compose_config = generator.generate()

        with open(COMPOSE_FILE, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)

    def generate_homepage_config(self) -> None:
        """Generate Homepage dashboard configuration."""
        if self.config.dashboard != "homepage":
            return

        homepage_dir = CONFIG_DIR / "homepage"
        homepage_dir.mkdir(parents=True, exist_ok=True)

        # Get local IP for service URLs
        try:
            result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
            ip = result.stdout.strip().split()[0]
        except Exception:
            ip = "localhost"

        # Build services config
        media_server = self.config.media_server
        media_ports = {"plex": 32400, "jellyfin": 8096, "emby": 8096}
        media_port = media_ports.get(media_server, 8096)

        services = [
            {
                "Media": [
                    {
                        media_server.title(): {
                            "icon": f"{media_server}.png",
                            "href": f"http://{ip}:{media_port}",
                            "description": "Media Server",
                        }
                    }
                ]
            },
            {
                "Management": [
                    {
                        "Radarr": {
                            "icon": "radarr.png",
                            "href": f"http://{ip}:7878",
                            "description": "Movie Management",
                        }
                    },
                    {
                        "Sonarr": {
                            "icon": "sonarr.png",
                            "href": f"http://{ip}:8989",
                            "description": "TV Show Management",
                        }
                    },
                    {
                        "Lidarr": {
                            "icon": "lidarr.png",
                            "href": f"http://{ip}:8686",
                            "description": "Music Management",
                        }
                    },
                    {
                        "Prowlarr": {
                            "icon": "prowlarr.png",
                            "href": f"http://{ip}:9696",
                            "description": "Indexer Management",
                        }
                    },
                ]
            },
        ]

        # Add request manager if configured
        req_mgr = self.config.request_manager
        if req_mgr != "none":
            req_ports = {"overseerr": 5055, "jellyseerr": 5055, "ombi": 3579}
            services[0]["Media"].append({
                req_mgr.title(): {
                    "icon": f"{req_mgr}.png",
                    "href": f"http://{ip}:{req_ports.get(req_mgr, 5055)}",
                    "description": "Request Manager",
                }
            })

        # Add downloaders
        downloaders = []
        if self.config.enable_torrents:
            downloaders.append({
                "qBittorrent": {
                    "icon": "qbittorrent.png",
                    "href": f"http://{ip}:8080",
                    "description": "Torrent Client",
                }
            })
        if self.config.enable_usenet:
            downloaders.append({
                "SABnzbd": {
                    "icon": "sabnzbd.png",
                    "href": f"http://{ip}:8080",
                    "description": "Usenet Client",
                }
            })
        if downloaders:
            services.append({"Downloads": downloaders})

        # Write services.yaml
        with open(homepage_dir / "services.yaml", "w") as f:
            yaml.dump(services, f, default_flow_style=False, sort_keys=False)

        # Write settings.yaml
        settings = {
            "title": "AstroMediaServer",
            "background": {
                "image": "",
                "blur": "sm",
                "opacity": 50,
            },
            "cardBlur": "sm",
            "theme": "dark",
            "color": "slate",
            "headerStyle": "clean",
            "layout": {
                "Media": {"style": "row", "columns": 2},
                "Management": {"style": "row", "columns": 4},
                "Downloads": {"style": "row", "columns": 2},
            },
        }
        with open(homepage_dir / "settings.yaml", "w") as f:
            yaml.dump(settings, f, default_flow_style=False, sort_keys=False)

        # Write widgets.yaml (system resources)
        widgets = [
            {"resources": {"cpu": True, "memory": True, "disk": "/"}},
            {"search": {"provider": "duckduckgo", "target": "_blank"}},
        ]
        with open(homepage_dir / "widgets.yaml", "w") as f:
            yaml.dump(widgets, f, default_flow_style=False, sort_keys=False)

        # Write empty bookmarks.yaml
        with open(homepage_dir / "bookmarks.yaml", "w") as f:
            f.write("# Add your bookmarks here\n[]")

        # Set ownership
        for f in homepage_dir.iterdir():
            os.chown(f, int(self.config.puid), int(self.config.pgid))
        os.chown(homepage_dir, int(self.config.puid), int(self.config.pgid))

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
            "overseerr": 5055,
            "jellyseerr": 5055,
            "ombi": 3579,
        }

        media_port = ports.get(self.config.media_server, 8096)
        dashboard_port = ports.get(self.config.dashboard, 3000)

        # Build request manager line if configured
        req_mgr = self.config.request_manager
        req_mgr_line = ""
        if req_mgr != "none":
            req_port = ports.get(req_mgr, 5055)
            req_mgr_line = f"\nRequests:      http://{ip}:{req_port}"

        completion_text = f"""
Setup Complete!

Your services are now running.

Access your server at:

Dashboard:     http://{ip}:{dashboard_port}
{self.config.media_server.title()}:      http://{ip}:{media_port}{req_mgr_line}
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
        self.ui.msgbox(completion_text, height=28, width=55)

    def run(self) -> int:
        """Run the setup wizard."""
        steps = [
            self.show_welcome,
            self.select_media_server,
            self.select_request_manager,
            self.select_download_method,
            self.select_downloader,
            self.select_gateway,
            self.select_dashboard,
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
