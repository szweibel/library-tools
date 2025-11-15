"""Claude Agent SDK adapter for library tools.

This module wraps the core framework-agnostic library tools for use with the
Claude Agent SDK. Each tool is wrapped with the @tool decorator to provide
proper type safety and integration with the Agent SDK's MCP server.

Installation:
    pip install library-tools[agent-sdk]

Usage:
    from library_tools.adapters.agent_sdk import (
        search_primo_tool,
        search_works_tool,
        # ... other tools
    )

    # Or use all tools via the MCP server
    from library_tools.adapters.agent_sdk import library_tools_server
"""

from typing import Any
from claude_agent_sdk import tool


# Primo Tools


@tool(
    "search_primo",
    "Search a library catalog using Ex Libris Primo to find books, journals, articles, and other resources",
    {
        "query": str,
        "field": str,  # "any", "title", "creator", "subject", "isbn", "issn"
        "operator": str,  # "contains", "exact"
        "limit": int,
        "start": int,
        "journals_only": bool,
    },
)
async def search_primo_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search Primo catalog."""
    from library_tools.primo.tool import search_primo

    result = await search_primo(
        query=args["query"],
        field=args.get("field", "any"),
        operator=args.get("operator", "contains"),
        limit=args.get("limit", 10),
        start=args.get("start", 0),
        journals_only=args.get("journals_only", False),
    )

    return {"content": [{"type": "text", "text": result}]}


# OpenAlex Tools


@tool(
    "search_works",
    "Search for academic publications using OpenAlex to find research papers, articles, and scholarly works",
    {
        "query": str,
        "limit": int,
        "page": int,
        "year_from": int,
        "open_access_only": bool,
    },
)
async def search_works_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search OpenAlex for academic works."""
    from library_tools.openalex.tools import search_works

    result = await search_works(
        query=args["query"],
        limit=args.get("limit", 10),
        page=args.get("page", 1),
        year_from=args.get("year_from"),
        open_access_only=args.get("open_access_only", False),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "search_authors",
    "Search for researchers and academics using OpenAlex by name or institution",
    {
        "name": str,
        "institution_id": str,
        "limit": int,
        "page": int,
    },
)
async def search_authors_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search OpenAlex for authors."""
    from library_tools.openalex.tools import search_authors

    result = await search_authors(
        name=args["name"],
        institution_id=args.get("institution_id"),
        limit=args.get("limit", 10),
        page=args.get("page", 1),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "get_author_works",
    "Get publications by a specific researcher using their OpenAlex author ID",
    {
        "author_id": str,
        "limit": int,
        "page": int,
    },
)
async def get_author_works_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get works by a specific author."""
    from library_tools.openalex.tools import get_author_works

    result = await get_author_works(
        author_id=args["author_id"],
        limit=args.get("limit", 10),
        page=args.get("page", 1),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "search_journals",
    "Search for academic journals and periodicals using OpenAlex",
    {
        "name": str,
        "limit": int,
        "page": int,
    },
)
async def search_journals_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search OpenAlex for journals."""
    from library_tools.openalex.tools import search_journals

    result = await search_journals(
        name=args["name"],
        limit=args.get("limit", 10),
        page=args.get("page", 1),
    )

    return {"content": [{"type": "text", "text": result}]}


# LibGuides Tools


@tool(
    "search_databases",
    "Search library databases using LibGuides A-Z list to find available databases by name or subject",
    {
        "search": str,
        "limit": int,
    },
)
async def search_databases_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search LibGuides databases."""
    from library_tools.libguides.tools import search_databases

    result = await search_databases(
        search=args.get("search"),
        limit=args.get("limit", 20),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "search_guides",
    "Search LibGuides to find research guides for subjects, courses, and topics",
    {
        "search": str,
        "guide_id": int,
        "limit": int,
    },
)
async def search_guides_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search LibGuides for research guides."""
    from library_tools.libguides.tools import search_guides

    result = await search_guides(
        search=args.get("search"),
        guide_id=args.get("guide_id"),
        limit=args.get("limit", 10),
    )

    return {"content": [{"type": "text", "text": result}]}


# Repository Tools


@tool(
    "search_repository",
    "Search an institutional repository (bePress/Digital Commons) for theses, dissertations, and scholarly works",
    {
        "query": str,
        "collection": str,
        "year": str,
        "limit": int,
        "start": int,
    },
)
async def search_repository_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search institutional repository."""
    from library_tools.repository.tools import search_repository

    result = await search_repository(
        query=args.get("query"),
        collection=args.get("collection"),
        year=args.get("year"),
        limit=args.get("limit", 50),
        start=args.get("start", 0),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "get_latest_repository_works",
    "Get the most recently added works from the institutional repository",
    {
        "collection": str,
        "limit": int,
        "start": int,
    },
)
async def get_latest_repository_works_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get latest works from repository."""
    from library_tools.repository.tools import get_latest_repository_works

    result = await get_latest_repository_works(
        collection=args.get("collection"),
        limit=args.get("limit", 50),
        start=args.get("start", 0),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "get_repository_work_details",
    "Get detailed information about a specific work in the repository using its URL",
    {
        "item_url": str,
    },
)
async def get_repository_work_details_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get details for a specific repository work."""
    from library_tools.repository.tools import get_repository_work_details

    result = await get_repository_work_details(
        item_url=args["item_url"],
    )

    return {"content": [{"type": "text", "text": result}]}


# WorldCat Tools


@tool(
    "lookup_worldcat_isbn",
    "Look up books in WorldCat to find ISBNs and bibliographic data using DOI, title, author, or ISBN",
    {
        "doi": str,
        "title": str,
        "author": str,
        "year": int,
        "isbn": str,
    },
)
async def lookup_worldcat_isbn_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Look up book in WorldCat."""
    from library_tools.worldcat.tools import lookup_worldcat_isbn

    result = await lookup_worldcat_isbn(
        doi=args.get("doi"),
        title=args.get("title"),
        author=args.get("author"),
        year=args.get("year"),
        isbn=args.get("isbn"),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "search_worldcat_books",
    "Search WorldCat for books by keyword or subject with optional filters for year and language",
    {
        "query": str,
        "year_from": int,
        "year_to": int,
        "language": str,
        "limit": int,
        "offset": int,
    },
)
async def search_worldcat_books_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search WorldCat for books."""
    from library_tools.worldcat.tools import search_worldcat_books

    result = await search_worldcat_books(
        query=args["query"],
        year_from=args.get("year_from"),
        year_to=args.get("year_to"),
        language=args.get("language"),
        limit=args.get("limit", 25),
        offset=args.get("offset", 1),
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "get_worldcat_classification",
    "Get Library of Congress and Dewey Decimal classification for a book using its OCLC number",
    {
        "oclc_number": str,
    },
)
async def get_worldcat_classification_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get classification for a WorldCat book."""
    from library_tools.worldcat.tools import get_worldcat_classification

    result = await get_worldcat_classification(
        oclc_number=args["oclc_number"],
    )

    return {"content": [{"type": "text", "text": result}]}


@tool(
    "get_worldcat_full_record",
    "Get complete bibliographic record with subjects, genres, and classification using OCLC number",
    {
        "oclc_number": str,
    },
)
async def get_worldcat_full_record_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get full bibliographic record from WorldCat."""
    from library_tools.worldcat.tools import get_worldcat_full_record

    result = await get_worldcat_full_record(
        oclc_number=args["oclc_number"],
    )

    return {"content": [{"type": "text", "text": result}]}


# Export all tools
__all__ = [
    "search_primo_tool",
    "search_works_tool",
    "search_authors_tool",
    "get_author_works_tool",
    "search_journals_tool",
    "search_databases_tool",
    "search_guides_tool",
    "search_repository_tool",
    "get_latest_repository_works_tool",
    "get_repository_work_details_tool",
    "lookup_worldcat_isbn_tool",
    "search_worldcat_books_tool",
    "get_worldcat_classification_tool",
    "get_worldcat_full_record_tool",
]
