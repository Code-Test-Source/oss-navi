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

## External API Research

### csdiy.wiki Integration

**Decision**: Scrape csdiy.wiki course catalog and cache locally.

**Implementation Approach**:
1. Fetch csdiy.wiki main page during sync
2. Parse course categories and links
3. Extract course metadata (name, topic, difficulty, link)
4. Cache as JSON in `~/.oss-navi/cache/csdiy.json`
5. Match courses to skill gaps during analysis

**Error Handling**:
- Graceful degradation if site unavailable
- Use cached data if available

### LeetCode API

**Decision**: Use LeetCode's GraphQL API for problem recommendations.

**API Endpoint**: `https://leetcode.com/graphql`

**Sample Query**:
```graphql
query {
  problemsetQuestionList(
    categorySlug: ""
    limit: 50
    filters: { difficulty: EASY, tags: ["array"] }
  ) {
    questions {
      title
      titleSlug
      difficulty
      topicTags { name }
    }
  }
}
```

### Codeforces API

**Decision**: Use Codeforces REST API for problem recommendations.

**API Endpoints**:
- `https://codeforces.com/api/problemset.problems` - Get all problems
- Rate limit: 5 requests per second

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
