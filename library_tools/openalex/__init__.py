"""OpenAlex academic publication search tools."""

from library_tools.openalex.client import (
    OpenAlexClient,
    OpenAlexWork,
    OpenAlexAuthor,
    OpenAlexJournal,
)
from library_tools.openalex.tools import (
    search_works,
    search_authors,
    get_author_works,
    search_journals,
)

__all__ = [
    "OpenAlexClient",
    "OpenAlexWork",
    "OpenAlexAuthor",
    "OpenAlexJournal",
    "search_works",
    "search_authors",
    "get_author_works",
    "search_journals",
]
