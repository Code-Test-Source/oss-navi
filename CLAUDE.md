# oss-navi Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-07

## Active Technologies
- Python 3.11+ + Click (CLI), httpx (HTTP client), httpx[socks] (SOCKS proxy), Pydantic v2 (data models), PyYAML (001-oss-discovery)
- JSON files in `~/.oss-navi/` (cache/, state/, temp/) (001-oss-discovery)
- Python 3.11+ + Click (CLI), httpx (HTTP client), Pydantic v2 (data models), PyYAML (config) (002-intelligent-recommendations)
- JSON files in `~/.oss-navi/` (cache/, state/, sessions/) (002-intelligent-recommendations)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 002-intelligent-recommendations: Added Python 3.11+
- 002-intelligent-recommendations: Added Python 3.11+ + Click (CLI), httpx (HTTP client), Pydantic v2 (data models), PyYAML (config)
- 001-oss-discovery: Added Python 3.11+ + Click (CLI), httpx (HTTP client), Pydantic v2 (data models), PyYAML

<!-- MANUAL ADDITIONS START -->
remember to do git commit every time you make changes
<!-- MANUAL ADDITIONS END -->
