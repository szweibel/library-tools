"""Library Tools - LLM tools for library and research services.

A collection of tools for Claude and other LLMs to search library catalogs,
academic publications, research databases, and institutional repositories.

Designed for use with Claude Agent SDK's @tool decorator pattern.
"""

__version__ = "0.1.0"

# Export tools for easy importing
from library_tools.primo.tool import search_primo
from library_tools.openalex.tools import (
    search_works,
    search_authors,
    get_author_works,
    search_journals,
)
from library_tools.libguides.tools import (
    search_databases,
    search_guides,
)
from library_tools.repository.tools import (
    search_repository,
    get_latest_repository_works,
    get_repository_work_details,
)

__all__ = [
    # Primo catalog search
    "search_primo",
    # OpenAlex academic search
    "search_works",
    "search_authors",
    "get_author_works",
    "search_journals",
    # LibGuides
    "search_databases",
    "search_guides",
    # Institutional repository
    "search_repository",
    "get_latest_repository_works",
    "get_repository_work_details",
]
