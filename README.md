# Library Tools

Python tools for searching library catalogs, academic databases, and institutional repositories. Returns formatted text suitable for use with language models or as standalone search utilities.

## What's Included

- **Primo** - Ex Libris library catalog search
- **OpenAlex** - Academic publications, authors, and journals
- **WorldCat** - OCLC global catalog with ISBN lookup
- **LibGuides** - SpringShare research guides and database lists
- **Repository** - bePress/Digital Commons institutional repositories

## Installation

```bash
# Using UV (recommended)
uv pip install library-tools

# Using pip
pip install library-tools

# With Claude Agent SDK adapter
uv pip install library-tools[agent-sdk]
```

## Setup

Create a `.env` file with credentials for the services you plan to use:

```bash
# Primo
PRIMO_API_KEY=your_api_key
PRIMO_VID=01INST:VIEW

# OpenAlex (optional email for better rate limits)
OPENALEX_EMAIL=your@email.com

# WorldCat
OCLC_CLIENT_ID=your_client_id
OCLC_CLIENT_SECRET=your_client_secret
OCLC_INSTITUTION_ID=CNY  # Optional

# LibGuides
LIBGUIDES_SITE_ID=123
LIBGUIDES_CLIENT_ID=456
LIBGUIDES_CLIENT_SECRET=secret

# Repository
REPOSITORY_BASE_URL=https://content-out.bepress.com/v2/your.repo.edu
REPOSITORY_API_KEY=your_key
```

## Basic Usage

```python
from library_tools.primo.tool import search_primo
from library_tools.openalex.tools import search_works
from library_tools.worldcat.tools import lookup_worldcat_isbn

# Search library catalog
result = await search_primo(
    query="artificial intelligence",
    limit=10
)

# Search academic papers
result = await search_works(
    query="machine learning",
    year_from=2020,
    limit=10
)

# Look up book by ISBN
result = await lookup_worldcat_isbn(
    isbn="9780451524935"
)
```

All functions return formatted strings. See the API reference below for available parameters.

## API Reference

### Primo

```python
from library_tools.primo.tool import search_primo

await search_primo(
    query: str,
    field: "any" | "title" | "creator" = "any",
    operator: "contains" | "exact" = "contains",
    limit: int = 10,
    start: int = 0,
    journals_only: bool = False
) -> str
```

### OpenAlex

```python
from library_tools.openalex.tools import (
    search_works,
    search_authors,
    get_author_works,
    search_journals,
)

await search_works(
    query: str,
    limit: int = 10,
    page: int = 1,
    year_from: int | None = None,
    open_access_only: bool = False
) -> str

await search_authors(
    name: str,
    institution_id: str | None = None,
    limit: int = 10,
    page: int = 1
) -> str

await get_author_works(
    author_id: str,
    limit: int = 10,
    page: int = 1
) -> str

await search_journals(
    name: str,
    limit: int = 10,
    page: int = 1
) -> str
```

### WorldCat

```python
from library_tools.worldcat.tools import (
    lookup_worldcat_isbn,
    search_worldcat_books,
    get_worldcat_classification,
    get_worldcat_full_record,
)

await lookup_worldcat_isbn(
    doi: str | None = None,
    title: str | None = None,
    author: str | None = None,
    year: int | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    isbn: str | None = None,
    fetch_holdings: bool = False,
    holdings_limit: int | None = None,
    check_institutions: list | None = None
) -> str

await search_worldcat_books(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    language: str | None = None,
    limit: int = 25,
    offset: int = 1,
    fetch_holdings: bool = False,
    holdings_limit: int | None = None,
    check_institutions: list | None = None
) -> str

await get_worldcat_classification(
    oclc_number: str
) -> str

await get_worldcat_full_record(
    oclc_number: str
) -> str
```

**Holdings Data:**
- Set `fetch_holdings=True` to get detailed institutional holdings information
- Use `holdings_limit` to control how many institutions to fetch (None = all)
- Use `check_institutions` to filter by specific institution codes (e.g., `["NYP", "DLC"]`)
- Returns institution codes, total holdings count, and availability details

```python
# Get complete holdings information (all institutions)
result = await lookup_worldcat_isbn(
    isbn="9780451524935",
    fetch_holdings=True
)

# Limit to first 100 holding institutions
result = await search_worldcat_books(
    query="climate change",
    fetch_holdings=True,
    holdings_limit=100
)

# Check if specific institutions hold the item
result = await lookup_worldcat_isbn(
    isbn="9780451524935",
    fetch_holdings=True,
    check_institutions=["NYP", "DLC", "HUH"]  # New York Public, Library of Congress, Harvard
)
```

### LibGuides

```python
from library_tools.libguides.tools import search_databases, search_guides

await search_databases(
    search: str | None = None,
    limit: int = 20
) -> str

await search_guides(
    search: str | None = None,
    guide_id: int | None = None,
    limit: int = 10
) -> str
```

### Institutional Repository

```python
from library_tools.repository.tools import (
    search_repository,
    get_latest_repository_works,
    get_repository_work_details,
)

await search_repository(
    query: str | None = None,
    collection: str | None = None,
    year: str | None = None,
    limit: int = 50,
    start: int = 0
) -> str

await get_latest_repository_works(
    collection: str | None = None,
    limit: int = 50,
    start: int = 0
) -> str

await get_repository_work_details(
    item_url: str
) -> str
```

## Pagination

Use pagination parameters to retrieve more than the default number of results:

- **Primo & Repository**: Use `start` (0-based offset: 0, 100, 200...)
- **OpenAlex**: Use `page` (page number: 1, 2, 3...)
- **WorldCat**: Use `offset` (1-based offset: 1, 51, 101...)

```python
# Example: Get multiple pages
for page in range(1, 4):
    result = await search_works(
        query="climate change",
        limit=100,
        page=page
    )
```

## Using with Claude Agent SDK

If you installed with `[agent-sdk]`, tools are already wrapped with the `@tool` decorator:

```python
from library_tools.adapters.agent_sdk import (
    search_primo_tool,
    search_works_tool,
    lookup_worldcat_isbn_tool,
)

# Use directly with Agent SDK
```

**Authentication:** When Claude Code is installed, the Claude Agent SDK uses Claude Code's authentication automatically (no API key required). Without Claude Code, set `ANTHROPIC_API_KEY` environment variable.

## Project Structure

```
library_tools/
├── primo/
│   ├── client.py      # API client (returns Pydantic models)
│   └── tool.py        # Tool wrapper (returns formatted strings)
├── openalex/
├── worldcat/
├── libguides/
├── repository/
├── common/
│   ├── config.py      # Environment configuration
│   └── errors.py      # Error handling
└── adapters/
    └── agent_sdk.py   # Claude Agent SDK adapter
```

Each service has two layers:
1. `client.py` - API interaction, returns Pydantic models
2. `tools.py` - Tool functions that format results as strings

## Configuration Details

### Primo

Required:
- `PRIMO_API_KEY` - API key from Ex Libris Developer Network
- `PRIMO_VID` - View ID (e.g., "01INST:VIEW")

Optional:
- `PRIMO_BASE_URL` - Custom API endpoint
- `PRIMO_SCOPE` - Search scope (default: "Everything")

### OpenAlex

No API key required. Optional:
- `OPENALEX_EMAIL` - Email for better rate limits (polite pool)

### WorldCat / OCLC

Required:
- `OCLC_CLIENT_ID` - Client ID from [OCLC Developer Network](https://platform.worldcat.org/wskey/)
- `OCLC_CLIENT_SECRET` - Client secret

Optional:
- `OCLC_INSTITUTION_ID` - Your institution's OCLC symbol (default: "CNY")

### LibGuides

Required:
- `LIBGUIDES_SITE_ID` - Site ID from LibApps admin
- `LIBGUIDES_CLIENT_ID` - OAuth client ID
- `LIBGUIDES_CLIENT_SECRET` - OAuth client secret

Optional:
- `LIBGUIDES_BASE_URL` - Custom endpoint

### Repository (bePress/Digital Commons)

Required:
- `REPOSITORY_BASE_URL` - API URL (e.g., `https://content-out.bepress.com/v2/institution.edu`)
- `REPOSITORY_API_KEY` - API security token

## Development

```bash
# Setup
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Test
pytest tests/

# Format and lint
black library_tools tests
ruff check library_tools
mypy library_tools
```

Tests hit live APIs and require valid credentials in `.env`. Some tests may fail due to rate limits.

## Writing Custom Adapters

To use with other frameworks, wrap the core tools:

```python
from library_tools.primo.tool import search_primo

async def my_adapter(params):
    result = await search_primo(
        query=params["query"],
        limit=params.get("limit", 10)
    )
    return {"response": result}
```

## Contributing

Keep these patterns when adding features:

1. Core tools are async functions with no framework dependencies
2. Use environment variables for configuration
3. Return error strings instead of raising exceptions
4. Include tests for new functionality
5. Add framework adapters in `adapters/` directory

## License

MIT
