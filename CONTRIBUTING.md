# Contributing to AstroMediaServer

Thank you for your interest in contributing to AstroMediaServer! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/UpstateNate/AstroMediaServer.git
   cd AstroMediaServer
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Ubuntu 22.04+ or Debian 12+ (native or WSL2)
- Python 3.10+
- Docker and Docker Compose v2
- Build tools: `xorriso`, `p7zip-full`, `genisoimage`

### Install Dependencies

```bash
# Build dependencies
sudo apt install xorriso p7zip-full wget genisoimage

# Runtime dependencies (for testing)
sudo apt install docker.io docker-compose-v2 python3 python3-yaml whiptail
```

### Testing the Setup Wizard

You can test the TUI wizard without building an ISO:

```bash
# Run the setup wizard (requires root for Docker)
sudo python3 scripts/astro-setup.py
```

### Building the ISO

```bash
./scripts/build-iso.sh

# Keep build artifacts for debugging
./scripts/build-iso.sh --keep-build
```

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
│   └── CHARTER.md         # Project specification
└── assets/                # Branding assets (future)
```

## Code Style

### Python
- Follow PEP 8
- Use type hints where practical
- Keep functions focused and under 50 lines
- Document complex logic with comments

### Bash
- Use `set -euo pipefail` at the start of scripts
- Quote all variables: `"$variable"`
- Use `[[ ]]` for conditionals
- Add comments for non-obvious commands

## Submitting Changes

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add NVIDIA hardware transcoding support

- Add nvidia-container-toolkit detection
- Configure Jellyfin/Plex with GPU passthrough
- Update docker-compose generator

Closes #42
```

Prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### Pull Requests

1. Update documentation if needed
2. Test your changes on a VM if possible
3. Ensure the ISO builds successfully
4. Create a PR with a clear description of changes

## Reporting Issues

When reporting bugs, please include:

- Host OS and version
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output (`/opt/astro/astro-init.log`)

## Feature Requests

Feature requests are welcome! Please:

1. Check existing issues first
2. Describe the use case
3. Explain how it fits the project goals

## Areas for Contribution

- **Hardware transcoding** - NVIDIA/Intel QSV support
- **VPN integration** - Route downloaders through VPN
- **Additional services** - Bazarr, Overseerr, Tautulli
- **Internationalization** - Timezone/locale improvements
- **Testing** - Automated testing framework
- **Documentation** - Tutorials, screenshots, videos

## Questions?

Open a discussion or issue - we're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
