"""MCP tools for PDF digest generation (TDD - Green Phase)."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.presentation.mcp.server import mcp
from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories.post_repository import PostRepository
from src.infrastructure.config.settings import get_settings
from src.infrastructure.llm.summarizer import summarize_posts as llm_summarize_posts
from src.infrastructure.monitoring.logger import get_logger

logger = get_logger(name="pdf_digest_tools")


async def _db():
    """Get database handle."""
    return await get_db()


@mcp.tool()
async def get_posts_from_db(user_id: int, hours: int = 24) -> Dict[str, Any]:
    """Retrieve posts from MongoDB grouped by channel.

    Purpose:
        Get posts for user's subscribed channels from database,
        grouped by channel with limits applied.

    Args:
        user_id: Telegram user ID
        hours: Hours to look back (default 24)

    Returns:
        Dict with posts_by_channel, total_posts, and channels_count

    Example:
        >>> result = await get_posts_from_db(user_id=1, hours=24)
        >>> print(result["channels_count"])
        5
    """
    settings = get_settings()
    db = await _db()
    repository = PostRepository(db)

    try:
        # Get posts for user's subscriptions
        all_posts = await repository.get_posts_by_user_subscriptions(user_id, hours=hours)

        # Group posts by channel
        posts_by_channel: Dict[str, List[dict]] = {}
        for post in all_posts:
            channel_name = post.get("channel_username")
            if channel_name:
                if channel_name not in posts_by_channel:
                    posts_by_channel[channel_name] = []
                posts_by_channel[channel_name].append(post)

        # Apply limits: max 100 posts per channel, max 10 channels
        limited_channels = {}
        sorted_channels = sorted(
            posts_by_channel.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )[: settings.digest_max_channels]

        total_posts = 0
        for channel_name, posts in sorted_channels:
            # Limit to max posts per channel
            limited_posts = posts[: settings.pdf_max_posts_per_channel]
            limited_channels[channel_name] = limited_posts
            total_posts += len(limited_posts)

        return {
            "posts_by_channel": limited_channels,
            "total_posts": total_posts,
            "channels_count": len(limited_channels),
        }
    except Exception as e:
        logger.error("Error retrieving posts from database", user_id=user_id, error=str(e), exc_info=True)
        return {"posts_by_channel": {}, "total_posts": 0, "channels_count": 0}


@mcp.tool()
async def summarize_posts(posts: List[dict], channel_username: str, max_sentences: int = 5) -> Dict[str, Any]:
    """Generate summary for posts from single channel using LLM.

    Purpose:
        Summarize posts for PDF digest with ML-engineer limits applied.

    Args:
        posts: List of post dictionaries with text, date, message_id
        channel_username: Channel username without @
        max_sentences: Maximum sentences per channel (default 5)

    Returns:
        Dict with summary, post_count, and channel

    Raises:
        None: Errors are logged and handled gracefully

    Example:
        >>> posts = [{"text": "Post 1", "date": datetime.utcnow(), "message_id": "1"}]
        >>> result = await summarize_posts(posts, "test_channel", max_sentences=5)
        >>> print(result["summary"])
        "Summary text here..."
    """
    settings = get_settings()
    max_posts = settings.pdf_max_posts_per_channel

    # Limit posts to max allowed
    limited_posts = posts[:max_posts] if len(posts) > max_posts else posts

    if not limited_posts:
        return {
            "summary": "Нет постов для саммари.",
            "post_count": 0,
            "channel": channel_username,
        }

    try:
        # Use existing summarizer with PDF-specific settings
        summary_text = await llm_summarize_posts(
            limited_posts,
            max_sentences=max_sentences or settings.pdf_summary_sentences,
        )

        # Enforce max characters limit
        if len(summary_text) > settings.pdf_summary_max_chars:
            summary_text = summary_text[: settings.pdf_summary_max_chars].rsplit(".", 1)[0] + "."

        return {
            "summary": summary_text,
            "post_count": len(limited_posts),
            "channel": channel_username,
        }
    except Exception as e:
        logger.error(
            "Error summarizing posts",
            channel=channel_username,
            post_count=len(limited_posts),
            error=str(e),
            exc_info=True,
        )
        # Fallback summary
        fallback = ". ".join([p.get("text", "")[:200] for p in limited_posts[:5]])
        return {
            "summary": fallback[: settings.pdf_summary_max_chars] if fallback else "Ошибка создания саммари.",
            "post_count": len(limited_posts),
            "channel": channel_username,
        }


def _render_markdown_template(summaries: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
    """Render markdown template for digest sections.

    Args:
        summaries: List of summary dicts with channel, summary, post_count
        metadata: Metadata dict with generation_date, user_id, etc.

    Returns:
        Markdown string with formatted sections
    """
    lines = []
    lines.append("# Channel Digest")
    lines.append("")

    generation_date = metadata.get("generation_date", datetime.utcnow().isoformat())
    lines.append(f"Generated: {generation_date}")
    total_posts = sum(s.get("post_count", 0) for s in summaries)
    lines.append(f"Channels: {len(summaries)} | Total Posts: {total_posts}")
    lines.append("")

    for summary in summaries:
        channel = summary.get("channel", "Unknown")
        summary_text = summary.get("summary", "")
        post_count = summary.get("post_count", 0)

        lines.append(f"## {channel}")
        lines.append("")
        lines.append(summary_text)
        lines.append("")
        lines.append(f"*Posts processed: {post_count}*")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def format_digest_markdown(summaries: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Format channel summaries into markdown section.

    Purpose:
        Convert summaries list into formatted markdown document.

    Args:
        summaries: List of summaries from summarize_posts
        metadata: Metadata dict with generation_date, user_id, etc.

    Returns:
        Dict with markdown and sections_count

    Example:
        >>> summaries = [{"channel": "ch1", "summary": "Summary", "post_count": 5}]
        >>> metadata = {"generation_date": "2024-01-15T20:00:00Z"}
        >>> result = await format_digest_markdown(summaries, metadata)
        >>> print(result["markdown"][:50])
        "# Channel Digest\n\nGenerated: 2024-01-15T20:00:00Z..."
    """
    try:
        markdown = _render_markdown_template(summaries, metadata)
        return {
            "markdown": markdown,
            "sections_count": len(summaries),
        }
    except Exception as e:
        logger.error("Error formatting markdown", error=str(e), exc_info=True)
        return {"markdown": "# Channel Digest\n\nError formatting digest.", "sections_count": 0}


def _load_template(template_name: str) -> str:
    """Load markdown template.

    Args:
        template_name: Template name (default: "default")

    Returns:
        Template string
    """
    templates = {
        "default": """# Telegram Channel Digest

Generated: {date}

---

{sections}

---

*End of digest*
""",
    }
    return templates.get(template_name, templates["default"])


@mcp.tool()
async def combine_markdown_sections(sections: List[str], template: str = "default") -> Dict[str, Any]:
    """Combine multiple markdown sections into single document with template.

    Purpose:
        Combine markdown sections with header and footer templates.

    Args:
        sections: List of markdown section strings
        template: Template name (default: "default")

    Returns:
        Dict with combined_markdown and total_chars

    Example:
        >>> sections = ["# Section 1\n\nContent", "# Section 2\n\nContent"]
        >>> result = await combine_markdown_sections(sections)
        >>> print(result["total_chars"])
        120
    """
    template_str = _load_template(template)
    combined_sections = "\n\n".join(sections)

    date_str = datetime.utcnow().isoformat()
    combined_markdown = template_str.format(date=date_str, sections=combined_sections)

    return {
        "combined_markdown": combined_markdown,
        "total_chars": len(combined_markdown),
    }


def _generate_css() -> str:
    """Generate CSS styling for PDF.

    Returns:
        CSS string with styling rules
    """
    return """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 1em;
            color: #000;
        }
        h2 {
            font-size: 18pt;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #222;
            page-break-after: avoid;
        }
        p {
            margin-bottom: 1em;
        }
        strong {
            font-weight: bold;
        }
        em {
            font-style: italic;
        }
    """


async def _convert_to_pdf(markdown_text: str, css: str) -> bytes:
    """Convert markdown to PDF bytes.

    Args:
        markdown_text: Markdown content
        css: CSS styling string

    Returns:
        PDF bytes

    Raises:
        Exception: If conversion fails
    """
    import markdown as md
    from weasyprint import HTML, CSS

    # Convert markdown to HTML
    html_content = md.markdown(markdown_text, extensions=["extra", "nl2br"])

    # Wrap in HTML document with CSS
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert to PDF
    pdf_bytes = HTML(string=full_html).write_pdf()
    return pdf_bytes


@mcp.tool()
async def convert_markdown_to_pdf(
    markdown: str, style: str = "default", metadata: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Convert markdown to PDF using weasyprint.

    Purpose:
        Generate PDF document from markdown content with styling.

    Args:
        markdown: Markdown content string
        style: Style name (default: "default")
        metadata: Optional metadata dict (not used currently)

    Returns:
        Dict with pdf_bytes (base64 encoded), file_size, and pages

    Raises:
        None: Errors are logged and returned in result dict

    Example:
        >>> markdown = "# Test\n\nContent"
        >>> result = await convert_markdown_to_pdf(markdown)
        >>> print(result["file_size"])
        1024
    """
    try:
        css = _generate_css()
        pdf_bytes = await _convert_to_pdf(markdown, css)

        # Encode to base64 for JSON serialization
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        # Estimate pages (rough: 1 page ≈ 3000 chars at 12pt)
        estimated_pages = max(1, len(markdown) // 3000 + 1)

        return {
            "pdf_bytes": pdf_base64,
            "file_size": len(pdf_bytes),
            "pages": estimated_pages,
        }
    except Exception as e:
        logger.error("Error converting markdown to PDF", error=str(e), style=style, exc_info=True)
        return {
            "pdf_bytes": "",
            "file_size": 0,
            "pages": 0,
            "error": str(e),
        }
