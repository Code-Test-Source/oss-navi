# OSS-Navi Project Structure

## Directory Layout

```
src/oss_navi/
├── cli.py              # Click CLI commands (sync, config, analysis, publish)
├── config.py           # Configuration management (proxy settings, token handling)
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

`config.py` provides centralized proxy and SSL settings used by both `github.py` and `scraper.py`:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Proxy Configuration                          │
├─────────────────────────────────────────────────────────────────┤
│  Environment Variables:                                          │
│  - HTTP_PROXY / http_proxy                                       │
│  - HTTPS_PROXY / https_proxy                                     │
│  - OSS_NAVI_VERIFY_SSL (default: true)                          │
├─────────────────────────────────────────────────────────────────┤
│                      ▲                                          │
│                      │                                          │
│           ┌─────────────────────────┐                          │
│           │      config.py          │                          │
│           │  get_proxy_settings()   │                          │
│           │  should_verify_ssl()    │                          │
│           └───────────┬─────────────┘                          │
│                       │                                          │
│           ┌───────────┴───────────┐                             │
│           │                       │                              │
│  ┌────────┴────────┐     ┌────────┴─────────┐                   │
│  │   github.py     │     │    scraper.py    │                   │
│  │ GitHubClient    │     │ create_http_     │                   │
│  │ ._create_client │     │ client()         │                   │
│  └─────────────────┘     │ create_async_    │                   │
│                          │ http_client()    │                   │
│                          └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

**IMPORTANT**: Proxy settings are centralized in `config.py`. When updating proxy handling:
1. Update `config.py`: `get_proxy_settings()` and `should_verify_ssl()`
2. Both `github.py` and `scraper.py` import from `config.py`

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
to configure a trusted CA bundle using standard TLS environment variables such as
`SSL_CERT_FILE` (single bundle file) or `SSL_CERT_DIR` (directory of certificates), or by
passing a CA bundle path to `verify=` when constructing the `httpx` client. This keeps
certificate validation active.

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

- [ ] If touching proxy code, update `config.py` first (centralized source)
- [ ] If adding new source name, update both cli.py and scraper.py
- [ ] If adding new cache type, update paths.py constants
- [ ] Run tests: `pytest --cov=oss_navi`
- [ ] Run linter: `ruff check src/`
