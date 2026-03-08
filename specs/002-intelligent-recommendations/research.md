# Research: Intelligent Recommendations & Learning Paths

**Feature**: 002-intelligent-recommendations
**Date**: 2026-03-08
**Updated**: 2026-03-08 (Added Surprise/LightFM, three modes)

## Algorithm Research

### Recommendation Modes

**Decision**: Implement three recommendation modes with varying algorithm complexity.

| Mode | Algorithms | Dependencies | Time | Memory |
|------|------------|--------------|------|--------|
| Fast | Content-based filtering | Pure Python | <30s | <50MB |
| Normal | Surprise SVD/KNN | scikit-surprise, numpy | <90s | <200MB |
| Thinking | LightFM + Apriori | lightfm, scikit-surprise, numpy | <180s | <500MB |

**Rationale**:
- Users have different needs (quick exploration vs deep analysis)
- Fast mode works without ML dependencies for lightweight installs
- Normal mode provides good quality with standard collaborative filtering
- Thinking mode delivers best results with hybrid approach

---

### Surprise (scikit-surprise) Integration

**Decision**: Use Surprise library for Normal and Thinking modes.

**Rationale**:
- Mature, well-documented library for collaborative filtering
- Implements SVD, KNN, and other matrix factorization algorithms
- Works well with user-item rating matrices
- Active community and maintained

**Algorithms to Use**:

1. **SVD (Singular Value Decomposition)**
   - Best for: Latent factor model, capturing user-project preferences
   - Use when: Sufficient user interaction data available
   - Parameters: n_factors=50, n_epochs=20, lr=0.005, reg=0.02

2. **KNNBasic (K-Nearest Neighbors)**
   - Best for: Finding similar users/projects
   - Use when: Sparse data, need interpretable recommendations
   - Parameters: k=20, sim_options={'name': 'cosine', 'user_based': True}

**Data Structure for Surprise**:
```python
from surprise import Dataset, Reader
from surprise.model_selection import train_test_split

# Create ratings from user interactions
# user_id, project_id, rating (1-5 based on fit score)
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(ratings_df[['user_id', 'project_id', 'rating']], reader)
```

---

### LightFM Integration

**Decision**: Use LightFM for Thinking mode hybrid recommendations.

**Rationale**:
- Hybrid approach combines collaborative + content-based filtering
- Supports implicit feedback (user interactions without explicit ratings)
- Handles cold-start users better than pure collaborative filtering
- Can incorporate user/project features (languages, topics)

**Algorithm Configuration**:
```python
from lightfm import LightFM
from lightfm.data import Dataset

# Create dataset with features
dataset = Dataset()
dataset.fit(users, items, user_features=user_features, item_features=item_features)

# Model with hybrid loss
model = LightFM(
    loss='warp',           # Weighted Approximate-Rank Pairwise
    no_components=64,      # Latent factors
    learning_rate=0.05,
    user_alpha=0.01,       # L2 regularization
    item_alpha=0.01
)
```

**Features to Include**:
- **User features**: Languages, skill levels, domain interests
- **Item features**: Project languages, topics, difficulty, stars

---

### Content-Based Filtering (Fast Mode)

**Decision**: Implement pure Python content-based filtering for Fast mode.

**Rationale**:
- No external dependencies required
- Fast execution (<30 seconds)
- Sufficient for quick exploration
- Works offline with cached data

**Implementation Approach**:
1. Build user skill vector from profile + preferences
2. Build project feature vectors from cached task data
3. Compute cosine similarity between vectors
4. Apply blocking rules and filters
5. Rank by similarity score

```python
def content_based_recommend(user_profile: dict, projects: list[dict]) -> list[Recommendation]:
    user_vector = build_skill_vector(user_profile)
    scores = []
    for project in projects:
        project_vector = build_project_vector(project)
        similarity = cosine_similarity(user_vector, project_vector)
        scores.append((project, similarity))
    return sorted(scores, key=lambda x: x[1], reverse=True)
```

---

### Apriori Pattern Mining

**Decision**: Implement Apriori for pattern discovery in Thinking mode.

**Rationale**:
- Discovers skill-project associations
- Provides explainable recommendations
- Works alongside LightFM for additional insights
- Pure Python implementation feasible

**Implementation**:
- Support threshold: 0.1 (10% of transactions)
- Confidence threshold: 0.5 (50% confidence)
- Max itemset size: 4 (to limit computation)

**Pattern Examples**:
- {python, web} → {django, fastapi} (confidence: 0.75)
- {go, distributed} → {kubernetes, etcd} (confidence: 0.68)

---

## External Data Source Research

### Data Source Strategy

**Decision**: Use third-party datasets as primary data source, API calls only for verification.

**Rationale**:
- Avoid rate limits (GitHub: 5000/hour, LeetCode/Codeforces also limited)
- Prevent appearing as DDoS attack
- Don't use user's account for large-scale scraping
- Only need minimal metadata for recommendations
- API calls reserved for verifying specific recommendations exist

**Data Flow**:
1. **Primary**: Load from third-party datasets during sync
2. **Secondary**: API calls only when user selects specific recommendations
3. **Verification**: Direct API call to confirm item exists before display

---

### LeetCode Data Sources

**Primary Dataset**: https://github.com/neenza/leetcode-problems

**Decision**: Clone/use this repository as primary LeetCode data source.

**Metadata to Extract** (minimal):
- Problem ID (titleSlug)
- Title
- Difficulty (Easy/Medium/Hard)
- Topics/Tags
- URL pattern: `https://leetcode.com/problems/{titleSlug}/`

**Alternative**: https://github.com/zhantong/leetcode-spider
- Can be used for more comprehensive scraping if needed
- Use sparingly to avoid rate limiting

**API Usage** (verification only):
- GraphQL endpoint: `https://leetcode.com/graphql`
- Only call when user requests specific problem details
- Use rate limiting: 1 request per 2 seconds

**Implementation**:
```python
# During sync: Load from dataset
def load_leetcode_dataset():
    # Clone or download from neenza/leetcode-problems
    # Parse JSON files
    # Extract: id, title, difficulty, tags
    # Cache to ~/.oss-navi/cache/leetcode.json
    pass

# During recommendation: Verify specific problem
def verify_leetcode_problem(title_slug: str) -> bool:
    # Single GraphQL query to verify problem exists
    # Rate limit: 1 per 2 seconds
    pass
```

---

### Codeforces Data Sources

**Primary Datasets**:

1. **Kaggle**: https://www.kaggle.com/datasets/lborgav/codeforces-problems
   - Comprehensive problem dataset
   - Includes: problem ID, rating, tags, difficulty

2. **Hugging Face**: https://huggingface.co/datasets/DenCT/codeforces-problems-7k
   - 7K problems with metadata
   - Easy to load with `datasets` library

**API Usage** (minimal metadata only):
- Endpoint: `https://codeforces.com/api/problemset.problems`
- Rate limit: 5 requests per second
- Only call once during sync for problem list (minimal data)
- No user-specific data needed

**Implementation**:
```python
# During sync: Load from dataset
def load_codeforces_dataset():
    # Option 1: Load from Kaggle dataset (if downloaded)
    # Option 2: Load from Hugging Face datasets library
    # Option 3: Single API call to problemset.problems
    # Extract: contestId, index, name, rating, tags
    # Cache to ~/.oss-navi/cache/codeforces.json
    pass

# API for minimal sync (once per sync, not per recommendation)
def sync_codeforces_problems():
    # Single GET request to problemset.problems
    # Returns all problems with minimal metadata
    # No authentication needed
    pass
```

---

### GitHub Data Sources

**Primary Dataset**: GitHub Archive - https://www.gharchive.org/

**Decision**: Use GitHub Archive for historical project data instead of live API.

**Rationale**:
- GitHub API rate limit: 5000 requests/hour (authenticated)
- GitHub Archive provides historical data without rate limits
- Can process offline at any time

**Data Available**:
- Repository events (stars, forks, issues)
- Commit activity
- Contributor patterns

**Implementation**:
```python
# During sync: Load from GitHub Archive
def load_github_archive_data(date_range: str):
    # Download hourly archives
    # Parse for project metadata
    # Extract: repo name, stars, language, topics
    # Cache to ~/.oss-navi/cache/github_archive.json
    pass
```

**API Usage** (verification only):
- When user selects a recommendation
- Verify repository still exists
- Get current issue count
- Rate limit: 1 request per second

---

### csdiy.wiki Integration

**Decision**: Scrape csdiy.wiki course catalog once and cache locally.

**Implementation Approach**:
1. Fetch csdiy.wiki main page during sync (once)
2. Parse course categories and links
3. Extract course metadata (name, topic, difficulty, link)
4. Cache as JSON in `~/.oss-navi/cache/csdiy.json`
5. Match courses to skill gaps during analysis

**Rate Limiting**:
- Single request per sync
- Use cached data for all subsequent analysis
- Add 2-second delay between requests if multiple pages needed

**Error Handling**:
- Graceful degradation if site unavailable
- Use cached data if available

---

## Scraping Best Practices

### Principles

**Decision**: Follow ethical scraping practices to avoid detection and respect services.

**Key Principles**:
1. **Use cached data locally** - Always prefer local cache over network requests
2. **Public metadata only** - Never use cookies, CSRF tokens, or authentication
3. **Rotate user agents** - Use `fake_useragent` to avoid detection
4. **Proxy support** - Allow proxy configuration for IP rotation
5. **Respect rate limits** - Never exceed reasonable request rates

---

### Implementation

#### User Agent Rotation

**Decision**: Use `fake_useragent` library for rotating user agents.

```python
from fake_useragent import UserAgent

# Configure httpx client with rotating user agent
ua = UserAgent()

headers = {
    "User-Agent": ua.random,  # Random browser user agent
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# With httpx
async with httpx.AsyncClient(headers=headers) as client:
    response = await client.get(url)
```

**Dependency**: Add `fake-useragent>=1.4.0` to pyproject.toml

---

#### Proxy Support

**Decision**: Support proxy configuration for IP rotation.

```python
# Proxy configuration in config or CLI
PROXY_CONFIG = {
    "http": "http://proxy.example.com:8080",
    "https": "http://proxy.example.com:8080",
}

# Or via environment variables (already supported by httpx)
# HTTP_PROXY, HTTPS_PROXY, NO_PROXY

# With httpx
async with httpx.AsyncClient(
    headers=headers,
    proxy=os.environ.get("HTTPS_PROXY"),  # Optional proxy
    timeout=30.0,
) as client:
    response = await client.get(url)
```

**CLI Option**:
```bash
oss-navi sync --learning --proxy http://localhost:8118
```

---

#### Public Metadata Only

**Decision**: Only fetch publicly available data without authentication.

**What we DON'T do**:
- ❌ Use cookies or session tokens
- ❌ Handle CSRF tokens
- ❌ Require user login for scraping
- ❌ Access authenticated endpoints
- ❌ Scrape user-specific data

**What we DO fetch**:
- ✅ Public problem lists (LeetCode, Codeforces)
- ✅ Public course catalogs (csdiy.wiki)
- ✅ Public repository metadata
- ✅ Public issue lists

```python
# Example: Public metadata only
def fetch_leetcode_problems():
    # Public GraphQL endpoint - no auth needed
    query = """
    query {
        problemsetQuestionList(limit: 100) {
            questions {
                title
                titleSlug
                difficulty
                topicTags { name }
            }
        }
    }
    """
    # No cookies, no tokens, just public data
    return graphql_request(query)
```

---

#### Local Cache First

**Decision**: Always check local cache before network request.

```python
def get_cached_or_fetch(cache_key: str, fetch_func: Callable, max_age_days: int = 7):
    """Get from cache if available and fresh, otherwise fetch."""
    cache_path = get_cache_path(cache_key)

    # Check cache first
    if cache_path.exists():
        cached = load_json(cache_path)
        age = datetime.now() - datetime.fromisoformat(cached["updated_at"])
        if age.days < max_age_days:
            return cached["data"]

    # Cache miss or stale - fetch with rate limiting
    data = fetch_func()
    save_json(cache_path, {"updated_at": datetime.now().isoformat(), "data": data})
    return data
```

---

### Rate Limiting Implementation

```python
import asyncio
from functools import wraps

class RateLimiter:
    """Enforce minimum delay between requests."""

    def __init__(self, min_delay: float = 2.0):
        self.min_delay = min_delay
        self.last_request = 0.0

    async def wait(self):
        """Wait if needed to respect rate limit."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            await asyncio.sleep(self.min_delay - elapsed)
        self.last_request = time.time()

# Per-domain rate limiters
RATE_LIMITERS = {
    "github": RateLimiter(min_delay=1.0),
    "leetcode": RateLimiter(min_delay=2.0),
    "codeforces": RateLimiter(min_delay=0.2),
    "csdiy": RateLimiter(min_delay=2.0),
    "default": RateLimiter(min_delay=2.0),
}
```

---

### Scraping Safety Checklist

- [ ] Use `fake_useragent` for all HTTP requests
- [ ] Check local cache before network request
- [ ] Only fetch public metadata (no auth/cookies)
- [ ] Respect rate limits (default 2s between requests)
- [ ] Support proxy configuration
- [ ] Handle graceful degradation on errors
- [ ] Cache all fetched data locally
- [ ] Log scraping activity for debugging

---

### Dependencies for Scraping

```toml
[project.optional-dependencies]
scrape = [
    "fake-useragent>=1.4.0",
]

# Already have: httpx[socks] for proxy support
```

**Note**: `httpx[socks]` already supports SOCKS proxies. Users can configure via environment variables.

---

### Data Sync Strategy

**Decision**: Implement staged sync with dataset priority.

**Sync Flow**:

```
┌─────────────────────────────────────────────────────────────┐
│                    SYNC COMMAND                              │
├─────────────────────────────────────────────────────────────┤
│  1. Load Third-Party Datasets (no rate limits)              │
│     ├── LeetCode: neenza/leetcode-problems                  │
│     ├── Codeforces: Kaggle or HuggingFace dataset           │
│     └── GitHub: GitHub Archive (optional)                   │
│                                                              │
│  2. Minimal API Calls (rate-limited)                        │
│     ├── Codeforces: problemset.problems (1 call)            │
│     └── csdiy.wiki: main page (1 call)                      │
│                                                              │
│  3. Cache to ~/.oss-navi/cache/                             │
│                                                              │
│  4. NO direct GitHub API calls during sync                   │
│     └── GitHub API reserved for verification only           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 RECOMMENDATION PHASE                         │
├─────────────────────────────────────────────────────────────┤
│  1. Generate recommendations from cached data                │
│                                                              │
│  2. User selects specific recommendation                     │
│                                                              │
│  3. Verify via API (rate-limited, 1 per 2 sec)              │
│     ├── LeetCode: Verify problem exists                      │
│     ├── Codeforces: Verify problem exists                    │
│     └── GitHub: Verify repo exists                           │
│                                                              │
│  4. Display verified recommendation                          │
└─────────────────────────────────────────────────────────────┘
```

---

### Rate Limiting Configuration

```python
# Rate limits enforced in code
RATE_LIMITS = {
    "github": {
        "requests_per_hour": 5000,
        "min_delay_seconds": 1.0,  # Conservative
        "burst_limit": 100,
    },
    "leetcode": {
        "requests_per_minute": 30,
        "min_delay_seconds": 2.0,  # Conservative
    },
    "codeforces": {
        "requests_per_second": 5,
        "min_delay_seconds": 0.2,
    },
    "general": {
        "min_delay_seconds": 2.0,  # Default for any API
    }
}
```

---

### Cached Data Structure

**LeetCode Cache** (`~/.oss-navi/cache/leetcode.json`):
```json
{
  "version": "1.0",
  "updated_at": "2026-03-08T...",
  "source": "neenza/leetcode-problems",
  "problems": [
    {
      "id": "two-sum",
      "title": "Two Sum",
      "difficulty": "Easy",
      "tags": ["array", "hash-table"],
      "url": "https://leetcode.com/problems/two-sum/"
    }
  ]
}
```

**Codeforces Cache** (`~/.oss-navi/cache/codeforces.json`):
```json
{
  "version": "1.0",
  "updated_at": "2026-03-08T...",
  "source": "kaggle/codeforces-problems",
  "problems": [
    {
      "contest_id": 4,
      "index": "A",
      "name": "Watermelon",
      "rating": 800,
      "tags": ["brute force", "math"],
      "url": "https://codeforces.com/problemset/problem/4/A"
    }
  ]
}
```

---

## Two-Round Language Matching

**Decision**: Implement two-round recommendation process as specified.

**Round 1**: Exact Language Match
1. User requests projects in language X
2. Scan cached JSON for projects with language X
3. If found → recommend with high priority
4. If not found → proceed to Round 2

**Round 2**: Adjacent Technologies
1. Mark language X as "learning prerequisite"
2. Find adjacent languages (based on similarity/category)
3. Recommend projects in adjacent languages
4. Include prerequisite courses for language X

**Language Adjacency Mapping**:
```python
LANGUAGE_ADJACENCY = {
    "rust": ["c", "cpp", "go"],
    "go": ["rust", "python", "java"],
    "python": ["javascript", "go", "ruby"],
    "typescript": ["javascript", "python"],
    "java": ["kotlin", "scala", "go"],
    "c": ["cpp", "rust", "go"],
    "cpp": ["c", "rust", "java"],
}
```

---

## Multi-Round Interactive Session Design

**Decision**: Implement stateful session management with JSON persistence.

**Session State Structure**:
```json
{
  "session_id": "uuid",
  "mode": "normal",
  "created_at": "2026-03-08T...",
  "user_preferences": {...},
  "rounds": [
    {
      "round_number": 1,
      "recommendations": [...],
      "user_feedback": [...],
      "selected_for_analysis": [...]
    }
  ],
  "report_sections": [...],
  "status": "active|completed"
}
```

---

## Performance Benchmarks

| Mode | Algorithm | Expected Time | Memory |
|------|-----------|---------------|--------|
| Fast | Content-based | 15-30s | 30-50MB |
| Normal | Surprise SVD | 60-90s | 100-200MB |
| Thinking | LightFM + Apriori | 120-180s | 300-500MB |

**Optimization Strategies**:
1. **Fast mode**: Pre-compute project vectors during sync
2. **Normal mode**: Cache trained model in `~/.oss-navi/cache/models/`
3. **Thinking mode**: Parallel computation where possible

---

## Dependencies Analysis

### Required for All Modes
- Python 3.11+
- Click, httpx, Pydantic v2, PyYAML

### Required for Normal Mode
```
scikit-surprise>=1.1.0
numpy>=1.24.0
```

### Required for Thinking Mode
```
lightfm>=1.17
scikit-surprise>=1.1.0
numpy>=1.24.0
```

### Installation Options
```bash
# Minimal (fast mode only)
pip install oss-navi

# With recommendation support
pip install oss-navi[recommend]

# Full installation
pip install oss-navi[recommend,dev]
```

---

## Alternatives Considered

### Pure Python Implementations (Rejected for Normal/Thinking)

**Rejected Because**:
- Surprise provides optimized SVD/KNN implementations
- LightFM's hybrid approach is well-tested
- Reinventing ML algorithms introduces bugs
- Performance would be worse without numpy

### Implicit Library (Considered)

**Rejected Because**:
- LightFM provides similar functionality
- LightFM has better documentation
- LightFM supports user/item features (important for our use case)

### TensorFlow/PyTorch (Rejected)

**Rejected Because**:
- Too heavy for a CLI tool
- Long installation time
- Not necessary for our scale
- Surprise/LightFM sufficient for collaborative filtering
