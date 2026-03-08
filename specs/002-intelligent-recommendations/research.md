# Research: Intelligent Recommendations & Learning Paths

**Feature**: 002-intelligent-recommendations
**Date**: 2026-03-08

## Algorithm Research

### Apriori Algorithm

**Decision**: Implement simplified Apriori for association rule mining on skill-project patterns.

**Rationale**:
- Classic algorithm for discovering frequent itemsets and association rules
- Well-suited for finding patterns like "users with Python skills → Django projects"
- Simple to implement in pure Python without heavy dependencies
- Works on cached JSON data - no real-time requirements

**Implementation Approach**:
1. Convert user profile skills to itemsets
2. Convert project requirements to itemsets
3. Find frequent itemsets with minimum support threshold
4. Generate association rules with minimum confidence threshold
5. Store discovered patterns for future recommendations

**Performance Considerations**:
- Run only on cached data (not real-time)
- Limit itemset size to 3-4 items to avoid combinatorial explosion
- Use transaction list format for memory efficiency
- Expected runtime: <5 seconds for typical cached data size

### FP-Growth Algorithm

**Decision**: Implement FP-Growth for efficient pattern discovery in larger datasets.

**Rationale**:
- More efficient than Apriori for large datasets (no candidate generation)
- FP-tree structure compresses data for memory efficiency
- Better suited when pattern database grows over time
- Pure Python implementation feasible for CLI tool

**Implementation Approach**:
1. Build FP-tree from cached transactions
2. Mine frequent patterns from FP-tree
3. Generate association rules from patterns
4. Cache patterns in `~/.oss-navi/state/patterns.json`

**Performance Considerations**:
- Build tree once per sync, cache results
- Tree depth limited by itemset size
- Memory efficient due to prefix sharing in tree structure
- Expected runtime: <3 seconds for typical data

### Collaborative Filtering

**Decision**: Implement user-based collaborative filtering using GitHub profile similarity.

**Rationale**:
- Leverages existing GitHub profile data
- Finds users with similar language/technology profiles
- Recommends projects those users contributed to
- Simple cosine similarity for user vectors

**Implementation Approach**:
1. Build user skill vectors from GitHub profiles
2. Compute similarity between users (cosine similarity)
3. Find top-k similar users
4. Aggregate their project contributions with weights
5. Rank projects by weighted contribution score

**Data Requirements**:
- User's own profile (from sync)
- Simulated/derived "similar user" profiles from public patterns
- Project contribution data from cached tasks

**Note**: Since we don't have a user database, we'll derive "similar user" patterns from:
- Public GitHub contributor data on recommended projects
- Language/topic distribution patterns from cached projects

### Content-Based Filtering

**Decision**: Implement content-based filtering using language and topic matching.

**Rationale**:
- Most straightforward approach for CLI tool
- Matches user's languages/skills to project requirements
- Already partially implemented in existing codebase
- Fast and lightweight

**Implementation Approach**:
1. Extract user's languages from GitHub profile + preferences
2. Extract project languages/topics from cached task data
3. Compute overlap score
4. Weight by user's skill level and learning interests
5. Apply blocking rules to filter results

## External API Research

### csdiy.wiki Integration

**Decision**: Scrape csdiy.wiki course catalog and cache locally.

**Rationale**:
- No official API available
- Static content, infrequently updated
- Valuable course recommendations organized by topic

**Implementation Approach**:
1. Fetch csdiy.wiki main page during sync
2. Parse course categories and links
3. Extract course metadata (name, topic, difficulty, link)
4. Cache as JSON in `~/.oss-navi/cache/csdiy.json`
5. Match courses to skill gaps during analysis

**Error Handling**:
- Graceful degradation if site unavailable
- Use cached data if available
- Report unavailability in output

### LeetCode API

**Decision**: Use LeetCode's unofficial GraphQL API for problem recommendations.

**Rationale**:
- Public GraphQL endpoint available
- Can query problems by topic and difficulty
- No authentication required for problem lists

**Implementation Approach**:
1. Query LeetCode GraphQL API for problems by topic
2. Filter by difficulty matching user skill level
3. Extract problem title, link, difficulty, topics
4. Cache problem list in `~/.oss-navi/cache/leetcode.json`
5. Match problems to skill gaps and learning interests

**API Endpoint**: `https://leetcode.com/graphql`

**Sample Query**:
```graphql
query {
  problemsetQuestionList(
    categorySlug: ""
    limit: 50
    skip: 0
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

**Error Handling**:
- Rate limit awareness (cache aggressively)
- Fallback to cached data
- Report unavailability gracefully

### Codeforces API

**Decision**: Use Codeforces official REST API for problem recommendations.

**Rationale**:
- Official public API available
- Well-documented and stable
- Can query problems by rating (difficulty) and tags

**Implementation Approach**:
1. Query Codeforces API for problemset
2. Filter by rating matching user skill level
3. Extract problem name, link, rating, tags
4. Cache problem list in `~/.oss-navi/cache/codeforces.json`
5. Match problems to skill gaps and learning interests

**API Endpoints**:
- `https://codeforces.com/api/problemset.problems` - Get all problems
- `https://codeforces.com/api/problemset.recentStatus` - Recent submissions

**Error Handling**:
- API rate limits: 5 requests per second
- Cache aggressively (problems don't change often)
- Graceful degradation if API unavailable

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

**Language Adjacency Mapping** (hardcoded, lightweight):
```python
LANGUAGE_ADJACENCY = {
    "rust": ["c", "cpp", "go"],
    "go": ["rust", "python", "java"],
    "python": ["javascript", "go", "ruby"],
    "typescript": ["javascript", "python"],
    # ... more mappings
}
```

## Multi-Round Interactive Session Design

**Decision**: Implement stateful session management with JSON persistence.

**Session Lifecycle**:
1. Start session → create session file with ID
2. Generate initial recommendations → store in session
3. User provides feedback → update session state
4. Generate refined recommendations → append to session
5. User modifies report → update session report sections
6. User stops → save final report, archive session

**Session State Structure**:
```json
{
  "session_id": "uuid",
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

**Performance**:
- Load session on each command invocation
- Save after each user action
- Keep session file small (<50KB typically)

## Performance Optimizations

**Goal**: Keep CLI lightweight and fast.

**Strategies**:
1. **Lazy Loading**: Only load data when needed
2. **Caching**: Cache all external API responses
3. **Algorithm Limits**: Cap itemset sizes, pattern counts
4. **Incremental Updates**: Only recompute what changed
5. **Background Sync**: Learning resources sync separately from analysis
6. **Minimal Dependencies**: Pure Python implementations

**Expected Performance**:
| Operation | Target Time |
|-----------|-------------|
| Initial analysis | <90 seconds |
| Interactive round | <5 seconds |
| Session load | <100ms |
| Session save | <50ms |
| Algorithm execution | <10 seconds total |
| Memory usage | <100MB |

## Alternatives Considered

### Machine Learning Libraries (scikit-learn, numpy)

**Rejected Because**:
- Heavy dependencies add ~50-100MB to package size
- Overkill for the scale of data we're working with
- Pure Python implementations sufficient for CLI use case
- Installation complexity increases for users

### Database Storage (SQLite, etc.)

**Rejected Because**:
- Adds complexity for simple JSON-serializable data
- JSON files sufficient for current scale
- Maintains simplicity and portability
- Easy debugging and manual inspection

### Real-time Collaborative Filtering

**Rejected Because**:
- Would require user database infrastructure
- Privacy concerns with storing user data centrally
- Simpler derived patterns sufficient for CLI tool
- Offline capability important for CLI use
