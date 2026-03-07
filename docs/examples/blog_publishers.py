"""Online blog publishing service (demonstration of challenges).

This module demonstrates why publishing to online blogs is complex.
Each platform requires different authentication, API calls, and content formats.

To actually implement this, you would need:
1. Platform-specific API clients
2. Secure credential storage for each platform
3. Content format converters (Markdown → HTML/Mobiledoc/Blocks)
4. Error handling for rate limits, API changes
5. Image upload handling (platforms don't accept image URLs)
"""

from dataclasses import dataclass
from enum import Enum


class BlogPlatform(Enum):
    """Supported blog platforms."""

    DEV_TO = "dev.to"
    MEDIUM = "medium"
    HASHNODE = "hashnode"
    WORDPRESS = "wordpress"
    GHOST = "ghost"
    NOTION = "notion"


@dataclass
class BlogCredentials:
    """Credentials for blog platforms - each requires different auth."""

    # Dev.to
    dev_to_api_key: str | None = None

    # Medium
    medium_integration_token: str | None = None
    medium_user_id: str | None = None

    # Hashnode
    hashnode_token: str | None = None
    hashnode_publication_id: str | None = None

    # WordPress
    wordpress_url: str | None = None
    wordpress_username: str | None = None
    wordpress_password: str | None = None  # Application password

    # Ghost
    ghost_url: str | None = None
    ghost_admin_api_key: str | None = None

    # Notion
    notion_integration_token: str | None = None
    notion_database_id: str | None = None


@dataclass
class BlogPost:
    """Normalized blog post structure."""

    title: str
    content: str  # Markdown, will be converted per platform
    tags: list[str]
    canonical_url: str | None = None
    cover_image: str | None = None


# Platform-specific challenges demonstrated below


class DevToPublisher:
    """Dev.to publisher - relatively simple but has quirks.

    Challenges:
    - Rate limits: 10 requests/30 seconds for unpublished
    - Cross-post detection: may flag as duplicate
    - Images: Must be hosted externally (no upload API)
    - Frontmatter: Specific YAML format required
    """

    API_BASE = "https://dev.to/api"

    def create_article(self, post: BlogPost, api_key: str) -> dict:
        """Create article on Dev.to.

        Requires specific frontmatter format:
        ---
        title: My Article
        published: false
        tags: python, rust
        ---
        """
        import httpx

        # Dev.to requires frontmatter in the body
        frontmatter = "---\n"
        frontmatter += f"title: {post.title}\n"
        frontmatter += "published: false\n"  # Create as draft first
        frontmatter += f"tags: {', '.join(post.tags[:4])}\n"  # Max 4 tags
        if post.cover_image:
            frontmatter += f"cover_image: {post.cover_image}\n"
        frontmatter += "---\n\n"

        body = frontmatter + post.content

        # API call
        response = httpx.post(
            f"{self.API_BASE}/articles",
            headers={"api-key": api_key},
            json={
                "article": {
                    "title": post.title,
                    "body_markdown": body,
                    "published": False,  # Start as draft
                    "tags": post.tags[:4],
                }
            },
        )

        if response.status_code == 401:
            raise ValueError("Invalid Dev.to API key")
        if response.status_code == 429:
            raise ValueError("Rate limited - wait 30 seconds")

        return response.json()


class MediumPublisher:
    """Medium publisher - NO MARKDOWN SUPPORT.

    Challenges:
    - Content MUST be HTML, not Markdown
    - No image upload API (images must be hosted)
    - Integration tokens expire
    - Cross-posting requires canonical URL
    - No draft mode via API - publishes immediately
    """

    API_BASE = "https://api.medium.com/v1"

    def create_post(self, post: BlogPost, token: str, user_id: str) -> dict:
        """Create post on Medium.

        MAJOR CHALLENGE: Medium does NOT accept Markdown.
        You must convert to HTML first.
        """
        import httpx

        # MUST convert Markdown to HTML
        html_content = self._markdown_to_html(post.content)

        response = httpx.post(
            f"{self.API_BASE}/users/{user_id}/posts",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "title": post.title,
                "contentFormat": "html",  # NOT markdown!
                "content": html_content,
                "tags": post.tags[:5],  # Max 5 tags
                "publishStatus": "draft",  # This doesn't exist - always publishes!
            },
        )

        # Medium API has no draft mode
        # This is a MAJOR limitation

        return response.json()

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML - required for Medium.

        This is a simplified conversion. Real implementation would need:
        - markdown-it or mistune library
        - Syntax highlighting for code blocks
        - Image handling
        - Table conversion
        """
        # Simplified example - real implementation is 100+ lines
        html = markdown.replace("\n\n", "</p><p>")
        html = f"<p>{html}</p>"
        # ... many more conversions needed
        return html


class HashnodePublisher:
    """Hashnode publisher - uses GraphQL.

    Challenges:
    - GraphQL API (more complex than REST)
    - Requires publication ID
    - Two-step process: create draft, then publish
    - Different mutation for each operation
    """

    API_URL = "https://gql.hashnode.com/"

    def create_draft(self, post: BlogPost, token: str, publication_id: str) -> dict:
        """Create draft using GraphQL mutation.

        GraphQL is more complex than REST - requires:
        - Precise query structure
        - Proper variable handling
        - Error parsing from GraphQL format
        """
        import httpx

        mutation = """
        mutation CreateDraft($input: CreateDraftInput!) {
            createDraft(input: $input) {
                draft {
                    id
                    title
                    slug
                }
            }
        }
        """

        variables = {
            "input": {
                "title": post.title,
                "contentMarkdown": post.content,
                "tags": [{"name": tag} for tag in post.tags],
                "publicationId": publication_id,
            }
        }

        response = httpx.post(
            self.API_URL,
            headers={"Authorization": token},
            json={"query": mutation, "variables": variables},
        )

        # GraphQL errors come in a different format
        data = response.json()
        if "errors" in data:
            raise ValueError(f"GraphQL error: {data['errors'][0]['message']}")

        return data["data"]["createDraft"]["draft"]


class WordPressPublisher:
    """WordPress publisher - REST API but with quirks.

    Challenges:
    - Application passwords (not regular password)
    - Plugin dependencies for some features
    - Media uploads are separate API calls
    - Different URL for each WordPress instance
    """

    def create_post(
        self,
        post: BlogPost,
        url: str,
        username: str,
        password: str,  # Application password, NOT user password
    ) -> dict:
        """Create WordPress post.

        Note: Requires Application Password, not regular password.
        Setup: WordPress Admin → Users → Profile → Application Passwords
        """
        import httpx

        response = httpx.post(
            f"{url}/wp-json/wp/v2/posts",
            auth=(username, password),  # Basic auth
            json={
                "title": post.title,
                "content": post.content,  # WordPress accepts Markdown with plugins
                "status": "draft",
                "tags": [],  # Tag IDs, not names - need lookup API
            },
        )

        return response.json()


class NotionPublisher:
    """Notion publisher - completely different paradigm.

    Challenges:
    - NOT a blogging platform - uses "database" as blog
    - Content is structured as "blocks", not Markdown
    - Each paragraph, heading, code block is a separate API call
    - No direct Markdown import
    - Must build content block by block
    """

    API_BASE = "https://api.notion.com/v1"

    def create_page(
        self,
        post: BlogPost,
        token: str,
        database_id: str,
    ) -> dict:
        """Create Notion page from Markdown.

        MAJOR CHALLENGE: Notion doesn't accept Markdown directly.
        You must convert to "blocks" format:

        Each paragraph, heading, list item, code block
        becomes a separate block object.

        A simple article might require 50+ API calls internally.
        """
        import httpx

        # Convert Markdown to Notion blocks
        blocks = self._markdown_to_blocks(post.content)

        response = httpx.post(
            f"{self.API_BASE}/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
            json={
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {"title": [{"text": {"content": post.title}}]},
                    "Tags": {"multi_select": [{"name": tag} for tag in post.tags]},
                },
                "children": blocks,  # Block objects, not Markdown
            },
        )

        return response.json()

    def _markdown_to_blocks(self, markdown: str) -> list[dict]:
        """Convert Markdown to Notion blocks.

        This is EXTREMELY complex. Example transformations:

        # Heading     → {"type": "heading_1", "heading_1": {"rich_text": [...]}}
        **bold**      → {"type": "text", "text": {"content": "bold"}, "annotations": {"bold": true}}
        `code`        → {"type": "text", "text": {"content": "code"}, "annotations": {"code": true}}
        ```python```  → {"type": "code", "code": {"rich_text": [...], "language": "python"}}

        Real implementation: 300+ lines for full Markdown support.
        """
        blocks = []

        # Simplified - each paragraph becomes a block
        for paragraph in markdown.split("\n\n"):
            blocks.append({
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": paragraph}}]
                }
            })

        return blocks


# Summary of challenges
CHALLENGES_SUMMARY = """
## Why Publishing to Online Blogs is Difficult

### 1. No Universal Standard
Each platform has its own:
- Authentication method (API key, OAuth, Basic auth)
- API format (REST, GraphQL)
- Content format (Markdown, HTML, Blocks)
- Rate limiting rules

### 2. Content Format Conversion
- Medium: HTML only (must convert from Markdown)
- Notion: Block-by-block (must parse and rebuild)
- Ghost: Mobiledoc format
- Dev.to: Markdown with specific frontmatter

### 3. Image Handling
No platform accepts image URLs for hosting:
- Images must be uploaded separately
- Each platform has different upload APIs
- Need to track and replace image URLs

### 4. Authentication Complexity
- Dev.to: Simple API key
- Medium: Integration token + user ID lookup
- WordPress: Application password per site
- Hashnode: Token + publication ID
- Notion: Integration token + database sharing

### 5. Draft vs Publish
- Medium: NO draft mode via API
- Dev.to: Draft supported
- WordPress: Draft supported
- Hashnode: Two-step draft → publish

### 6. Rate Limits
- Dev.to: 10 requests/30 seconds
- Medium: 1 request/second
- WordPress: Varies by hosting
- Notion: 3 requests/second

## Possible Solutions

### Option 1: Platform-Specific Publishers
Implement separate publisher for each platform.
- Pros: Full control, all features
- Cons: High maintenance, API changes break things

### Option 2: Use Static Site Generator
Push to GitHub, let GitHub Pages/Vercel handle publishing.
- Pros: Single integration, free hosting
- Cons: Not a "real" blog platform, slower updates

### Option 3: Webhook/Integration
Push to GitHub, trigger webhook to blog platform.
- Pros: Decoupled, extensible
- Cons: More infrastructure needed

### Option 4: Use a Unified API
Services like BlogFox or custom middleware.
- Pros: Single interface
- Cons: Another dependency, may have costs

### Option 5: Support Just One Platform
Focus on Dev.to (simplest API) or Hashnode (popular with devs).
- Pros: Maintainable
- Cons: Limits user choice
"""
