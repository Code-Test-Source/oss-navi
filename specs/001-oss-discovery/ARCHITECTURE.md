# OSS-Navi Project Structure

## Directory Layout

```
src/oss_navi/
├── cli.py              # Click CLI commands (sync, config, analysis, publish)
├── models/             # Pydantic data models
│   ├── config.py       # Config model
│   ├── task.py         # Task, Repository models
│   └── user_profile.py # UserProfile, Activity, Repository models
├── services/           # Business logic
│   ├── github.py       # GitHub API client
│   └── scraper.py      # Task scraping (Up For Grabs, Good First Issues)
└── utils/              # Helper utilities
    ├── cache.py        # JSON read/write for cache
    ├── paths.py        # Path constants (~/.oss-navi/)
    └── memory.py       # Long-term memory persistence
```

## Key Relationships

### HTTP Client Pattern

Both `github.py` and `scraper.py` create httpx clients with proxy support:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Proxy Configuration                          │
├─────────────────────────────────────────────────────────────────┤
│  Environment Variables:                                          │
│  - HTTP_PROXY / http_proxy                                       │
│  - HTTPS_PROXY / https_proxy                                     │
│  - OSS_NAVI_VERIFY_SSL (default: true)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────────┐               │
│  │   github.py     │     │    scraper.py       │               │
│  │ GitHubClient    │     │ create_http_client  │               │
│  │ ._create_client │     │ create_async_client │               │
│  └────────┬────────┘     └──────────┬──────────┘               │
│           │                         │                           │
│           └──────────┬──────────────┘                           │
│                      ▼                                          │
│           ┌─────────────────────────┐                          │
│           │  httpx.Client/AsyncClient │                         │
│           │  with mounts for proxies  │                         │
│           │  verify=should_verify_ssl()│                        │
│           └─────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

**IMPORTANT**: When updating proxy handling, update ALL THREE functions:
1. `github.py`: `GitHubClient._create_client()`
2. `scraper.py`: `create_http_client()`
3. `scraper.py`: `create_async_http_client()`

### Source Names

Both CLI and scraper must use consistent source names:

| Source Name (string) | Used In |
|---------------------|---------|
| `upforgrabs` | cli.py, scraper.py |
| `goodfirstissues` | cli.py, scraper.py |

Cache metadata keys:
- `upforgrabs_tasks`
- `goodfirstissues_tasks`

### Data Flow

```
┌──────────┐    ┌──────────────┐    ┌─────────────┐
│  CLI     │───▶│   Services   │───▶│   Utils     │
│  sync    │    │   scraper    │    │   cache     │
└──────────┘    └──────────────┘    └─────────────┘
                     │
                     ▼
              ┌──────────────────────────────────┐
              │  Cache Files (~/.oss-navi/cache/) │
              │  - github_profile.json            │
              │  - upforgrabs_tasks.json          │
              │  - goodfirstissues_tasks.json     │
              └──────────────────────────────────┘
```

## Common Patterns

### Adding a New HTTP Client

When creating any httpx client with proxy support, use helpers from `oss_navi.config`:

```python
from oss_navi.config import get_proxy_settings, should_verify_ssl

def create_client(timeout: float) -> httpx.Client:
    proxy_settings = get_proxy_settings()  # env vars take precedence over config file
    http_proxy = proxy_settings["http_proxy"]
    https_proxy = proxy_settings["https_proxy"]
    verify_ssl = should_verify_ssl()

    if https_proxy and http_proxy:
        return httpx.Client(
            timeout=timeout,
            verify=verify_ssl,
            mounts={
                "http://": httpx.HTTPTransport(proxy=http_proxy, verify=verify_ssl),
                "https://": httpx.HTTPTransport(proxy=https_proxy, verify=verify_ssl),
            }
        )
    elif https_proxy:
        return httpx.Client(timeout=timeout, verify=verify_ssl, proxy=https_proxy)
    elif http_proxy:
        return httpx.Client(timeout=timeout, verify=verify_ssl, proxy=http_proxy)
    else:
        return httpx.Client(timeout=timeout, verify=verify_ssl)
```

**SSL Verification**: `should_verify_ssl()` reads `OSS_NAVI_VERIFY_SSL` from the environment.
Setting `OSS_NAVI_VERIFY_SSL=false` disables certificate validation — use this only as a
last resort. For corporate proxies with self-signed certificates, the preferred approach is
to configure a trusted CA bundle via `REQUESTS_CA_BUNDLE` or `SSL_CERT_FILE` environment
variables, which keeps certificate validation active.

### Async Client Pattern

Same pattern but with `AsyncClient` and `AsyncHTTPTransport`:

```python
return httpx.AsyncClient(
    timeout=timeout,
    verify=verify_ssl,
    mounts={
        "http://": httpx.AsyncHTTPTransport(proxy=http_proxy, verify=verify_ssl),
        "https://": httpx.AsyncHTTPTransport(proxy=https_proxy, verify=verify_ssl),
    }
)
```

## Checklist Before Editing

- [ ] If touching proxy code, update ALL client creation functions
- [ ] If adding new source name, update both cli.py and scraper.py
- [ ] If adding new cache type, update paths.py constants
- [ ] Run tests: `pytest --cov=oss_navi`
- [ ] Run linter: `ruff check src/`
