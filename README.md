# OSS-Navi

> A CLI tool that helps programmers discover and contribute to open source projects

OSS-Navi analyzes your GitHub profile, scrapes beginner-friendly issues from multiple sources, and generates personalized project recommendations using Claude Code.

## Features

- **Profile Analysis**: Fetch and analyze your GitHub profile (commits, languages, activity)
- **Task Discovery**: Scrape open source tasks from Up For Grabs and Good First Issue
- **Smart Filtering**: Filter tasks by stars, recency, and compute a "hotness" score
- **Learning Focus**: Specify what you're currently learning with `--learn` flag
- **AI Recommendations**: Generate personalized recommendations with Claude Code
- **Report Archiving**: Archive and optionally publish reports to your blog

## Installation

```bash
# Clone the repository
git clone https://github.com/user/oss-navi.git
cd oss-navi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Quick Start

```bash
# Configure your GitHub credentials
oss-navi config --github-username your-username
oss-navi config --github-token ghp_your_token_here

# Sync your profile and available tasks
oss-navi sync

# Generate personalized recommendations
oss-navi analysis

# Focus on learning a specific technology
oss-navi analysis --learn rust
```

## Commands

| Command | Description |
|---------|-------------|
| `config` | Manage configuration settings |
| `sync` | Fetch GitHub profile and task data |
| `analysis` | Generate personalized recommendations |
| `publish` | Archive and publish reports |

## Configuration

All data is stored under `~/.oss-navi/`:

```
~/.oss-navi/
├── .token              # GitHub token (secure)
├── cache/              # Cached data (24h expiration)
│   ├── github_profile.json
│   └── tasks.json
├── state/              # Persistent data
│   ├── config.json
│   ├── memory.json
│   └── reports/
└── temp/               # Temporary files
```

## Requirements

- Python 3.11+
- GitHub Personal Access Token
- Claude Code installed locally

## License

MIT
