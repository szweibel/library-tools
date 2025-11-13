# Library Tools

Framework-agnostic LLM tools for searching library catalogs, academic publications, research databases, and institutional repositories.

**Design Philosophy**: Core tools are plain async functions with no framework dependencies. Optional adapters are provided for specific LLM frameworks (Claude Agent SDK).

## Features

- **Primo Catalog Search** - Search library catalogs using Ex Libris Primo
- **OpenAlex Academic Search** - Search scholarly works, authors, and journals
- **LibGuides** - Search research guides and database A-Z lists
- **Institutional Repository** - Search bePress/Digital Commons repositories

## Installation

```bash
# Using UV (recommended)
uv pip install library-tools

# Using pip
pip install library-tools

# With Claude Agent SDK adapter
uv pip install library-tools[agent-sdk]
```

## Quick Start

### 1. Configure Environment Variables

Create a `.env` file with your API credentials:

```bash
# Primo (Library Catalog)
PRIMO_API_KEY=your_api_key
PRIMO_VID=01INST:VIEW

# OpenAlex (Academic Publications)
OPENALEX_EMAIL=your@email.com

# LibGuides (Research Guides)
LIBGUIDES_SITE_ID=123
LIBGUIDES_CLIENT_ID=456
LIBGUIDES_CLIENT_SECRET=secret

# Repository (Institutional Repository)
REPOSITORY_BASE_URL=https://content-out.bepress.com/v2/your.repo.edu
REPOSITORY_API_KEY=your_key
```

### 2. Using the Core Tools (Framework-Agnostic)

The core tools are plain async functions that work with any LLM framework:

```python
from library_tools.primo.tool import search_primo
from library_tools.openalex.tools import search_works, search_authors
from library_tools.libguides.tools import search_databases, search_guides
from library_tools.repository.tools import search_repository

# Example: Search library catalog
result = await search_primo(
    query="artificial intelligence",
    field="any",
    limit=10
)
print(result)  # Returns formatted string

# Example: Search academic papers
result = await search_works(
    query="machine learning",
    year_from=2020,
    open_access_only=True,
    limit=10
)
print(result)

# Example: Search research guides
result = await search_guides(search="psychology")
print(result)
```

### 3. Using with Claude Agent SDK

If you've installed the `agent-sdk` extra, use the pre-wrapped tools:

```python
from library_tools.adapters.agent_sdk import (
    search_primo_tool,
    search_works_tool,
    search_authors_tool,
    search_databases_tool,
    search_guides_tool,
    search_repository_tool,
)

# These tools are already decorated with @tool for Agent SDK compatibility
# Use them directly with the Claude Agent SDK
```

## Configuration

All configuration is loaded from environment variables. Each tool suite requires different settings.

### Primo (Library Catalog)

**Required:**
- `PRIMO_API_KEY` - Your Ex Libris Primo API key
- `PRIMO_VID` - View ID (e.g., "01INST:VIEW")

**Optional:**
- `PRIMO_BASE_URL` - API endpoint (default: Ex Libris hosted)
- `PRIMO_SCOPE` - Search scope (default: "Everything")

### OpenAlex (Academic Publications)

**Optional:**
- `OPENALEX_EMAIL` - Your email for polite pool (better rate limits)

No API key required - OpenAlex is free and open!

### LibGuides (Research Guides & Databases)

**Required:**
- `LIBGUIDES_SITE_ID` - Your LibGuides site ID
- `LIBGUIDES_CLIENT_ID` - OAuth client ID
- `LIBGUIDES_CLIENT_SECRET` - OAuth client secret

**Optional:**
- `LIBGUIDES_BASE_URL` - API endpoint (default: lgapi-us.libapps.com/1.2)

### Repository (Institutional Repository)

**Required:**
- `REPOSITORY_BASE_URL` - Repository API base URL
  - Example: `https://content-out.bepress.com/v2/academicworks.cuny.edu`
- `REPOSITORY_API_KEY` - API security token

## Available Tools

### Primo Catalog Search

```python
from library_tools.primo.tool import search_primo

await search_primo(
    query: str,                          # Search terms
    field: "any" | "title" | "creator",  # Search field
    operator: "contains" | "exact",      # Match type
    limit: int = 10,                     # Max results (1-100)
    start: int = 0,                      # Pagination offset
    journals_only: bool = False          # Journals only
) -> str
# Returns: Publisher, ISBN/ISSN, availability, links
```

### OpenAlex Academic Search

```python
from library_tools.openalex.tools import (
    search_works,
    search_authors,
    get_author_works,
    search_journals,
)

# Search publications
await search_works(
    query: str,                    # Research topic
    limit: int = 10,              # Max results per page (1-100)
    page: int = 1,                # Page number for pagination
    year_from: int | None = None, # Filter by year
    open_access_only: bool = False
) -> str
# Returns: Work ID, ALL authors, citations, DOI, abstract

# Search researchers
await search_authors(
    name: str,                     # Author name
    institution_id: str | None,   # Filter by institution
    limit: int = 10,              # Max results per page (1-100)
    page: int = 1                 # Page number for pagination
) -> str
# Returns: Author ID, metrics, institution

# Get author's publications
await get_author_works(
    author_id: str,                # OpenAlex author ID
    limit: int = 10,              # Max results per page (1-200)
    page: int = 1                 # Page number for pagination
) -> str
# Returns: Complete publication list with all metadata

# Search journals
await search_journals(
    name: str,                     # Journal name
    limit: int = 10,              # Max results per page (1-100)
    page: int = 1                 # Page number for pagination
) -> str
# Returns: ISSN, publisher, metrics
```

### LibGuides

```python
from library_tools.libguides.tools import search_databases, search_guides

# Search database A-Z list
await search_databases(
    search: str | None = None,     # Database name or topic
    limit: int = 20                # Max results (1-100)
) -> str
# Returns: Database ID, vendor, alternative names, subjects, types

# Search research guides
await search_guides(
    search: str | None = None,     # Subject or course
    guide_id: int | None = None,   # Specific guide ID
    limit: int = 10                # Max results (1-100)
) -> str
# Returns: Guide ID, status, owner, all pages/tabs
```

### Institutional Repository

```python
from library_tools.repository.tools import (
    search_repository,
    get_latest_repository_works,
    get_repository_work_details,
)

# Search repository
await search_repository(
    query: str | None = None,      # Keywords
    collection: str | None = None, # Collection code
    year: str | None = None,       # Publication year
    limit: int = 50,              # Max results (1-1000)
    start: int = 0                # Pagination offset
) -> str
# Returns: ALL authors, collection code, fulltext URL, landing page URL

# Get latest works
await get_latest_repository_works(
    collection: str | None = None,
    limit: int = 50,              # Max results (1-1000)
    start: int = 0                # Pagination offset
) -> str
# Returns: Complete metadata for recent additions

# Get work details
await get_repository_work_details(
    item_url: str                   # Full work URL
) -> str
# Returns: Full abstract, ALL keywords, advisor, publication info
```

## Design Principles

### Framework-Agnostic

Core tools are plain async functions with no framework dependencies. They return formatted strings suitable for any LLM framework. Optional adapters are provided for specific frameworks:

- **Agent SDK adapter** (`library_tools.adapters.agent_sdk`) - For Claude Agent SDK
- More adapters can be added by the community

### Institution-Agnostic

All tools work with any institution's instance of these services. Configuration is handled through environment variables, with no hardcoded institution-specific values.

### Comprehensive Data for LLM Decision-Making

All tools provide complete metadata to enable confident LLM decision-making:
- **ALL available metadata** is included (authors, identifiers, URLs, etc.)
- **Pagination support** for exhaustive searches across hundreds/thousands of results
- **Unique identifiers** (Work IDs, Author IDs, Database IDs) for follow-up queries
- **Structured text format** with clear headers for easy parsing
- **Helpful error messages** instead of exceptions

**Philosophy**: LLMs need comprehensive data to make informed decisions, not human-friendly summaries. The tools provide:
- Full author lists (not truncated to "et al.")
- Complete keyword sets
- Both landing page and fulltext URLs
- Collection codes and names
- Publisher information, ISBNs, ISSNs
- All available metrics (citations, h-index, etc.)

**Pagination**: All tools support retrieving results beyond the first page:
- Primo & Repository: Use `start` parameter (offset-based, e.g., start=0, start=100, start=200)
- OpenAlex: Use `page` parameter (page-based, e.g., page=1, page=2, page=3)
- LibGuides: Limited pagination (fetches all, filters client-side)

### Two-Layer Architecture

Each service has two layers:
1. **Client** (`client.py`) - Pure API logic, returns Pydantic models
2. **Tools** (`tools.py` or `tool.py`) - LLM tool functions that format client results as strings

This separation allows you to:
- Use clients directly for programmatic access with type-safe models
- Use tools for LLM integration with pre-formatted text output
- Create your own adapters for other LLM frameworks

## Architecture

```
library-tools/
├── library_tools/
│   ├── primo/
│   │   ├── client.py      # Primo API client (returns Pydantic models)
│   │   └── tool.py        # LLM tool wrapper (returns formatted strings)
│   ├── openalex/
│   │   ├── client.py      # OpenAlex API client
│   │   └── tools.py       # LLM tool wrappers
│   ├── libguides/
│   │   ├── client.py      # LibGuides API client
│   │   └── tools.py       # LLM tool wrappers
│   ├── repository/
│   │   ├── client.py      # Repository API client
│   │   └── tools.py       # LLM tool wrappers
│   ├── common/
│   │   ├── config.py      # Environment configuration
│   │   └── errors.py      # Error handling
│   └── adapters/
│       └── agent_sdk.py   # Claude Agent SDK adapter
```

## Using Adapters

### Claude Agent SDK

```python
from library_tools.adapters.agent_sdk import (
    search_primo_tool,
    search_works_tool,
    search_databases_tool,
    # ... all 10 tools
)

# Tools are already wrapped with @tool decorator
# and ready to use with Agent SDK's MCP server
```

### Creating Custom Adapters

You can create adapters for other frameworks by wrapping the core tools:

```python
from library_tools.primo.tool import search_primo

# Example: Custom adapter for your framework
async def my_framework_search_primo(params):
    result = await search_primo(
        query=params["query"],
        limit=params.get("limit", 10)
    )
    return {"response": result}  # Format for your framework
```

## Development

```bash
# Create virtual environment with UV
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"

# Run tests (live integration tests hitting real APIs)
pytest tests/

# Run specific test suite
pytest tests/test_openalex_live.py

# Format code
black library_tools tests

# Type checking
mypy library_tools

# Lint
ruff check library_tools
```

## Testing

The test suite includes live integration tests that hit actual APIs:

- `tests/test_primo_live.py` - Tests Primo API (may hit rate limits in parallel)
- `tests/test_openalex_live.py` - Tests OpenAlex API
- `tests/test_libguides_live.py` - Tests LibGuides API
- `tests/test_repository_live.py` - Tests repository API

**Note:** Tests require valid credentials in `.env`. Some tests may fail due to API rate limits when run in parallel - this is expected behavior.

## Examples

### Basic Search

```python
from library_tools.primo.tool import search_primo

# Simple search
result = await search_primo("machine learning", limit=10)
print(result)
```

### Comprehensive Search with Pagination

```python
from library_tools.openalex.tools import search_works

# Exhaustive search across multiple pages
all_works = []
for page in range(1, 6):  # Get first 5 pages (500 results)
    result = await search_works(
        query="climate change",
        limit=100,
        page=page,
        year_from=2020
    )
    all_works.append(result)
    # LLM can now analyze all 500 results to find most relevant
```

### Repository Pagination

```python
from library_tools.repository.tools import search_repository

# Get all theses in a collection
all_theses = []
start = 0
while True:
    result = await search_repository(
        collection="gc_etds",
        limit=100,
        start=start
    )
    if "Found 0" in result or "No works" in result:
        break
    all_theses.append(result)
    start += 100
```

### Using Identifiers for Follow-up Queries

```python
from library_tools.openalex.tools import search_authors, get_author_works

# Find researcher
authors = await search_authors("Jane Smith", limit=5)
# Extract author ID from results (e.g., "ID: https://openalex.org/A1234567890")

# Get all their publications
works = await get_author_works(
    author_id="A1234567890",
    limit=200,  # Repository supports up to 200 per page
    page=1
)
```

### Complete Metadata for Decision Making

```python
from library_tools.repository.tools import get_repository_work_details

# Get full details including complete abstract, all keywords
details = await get_repository_work_details(
    item_url="https://academicworks.cuny.edu/gc_etds/1234"
)
# Returns: Full abstract (not truncated), all keywords, advisor,
# fulltext URL, collection code, all authors
```

See the `examples/` directory for more complete usage examples:
- `basic_search.py` - Simple catalog and academic searches
- `multi_tool.py` - Using multiple tools together
- `agent_integration.py` - Full Claude Agent SDK integration
- `comprehensive_search.py` - Pagination and exhaustive searches

## License

MIT

## Contributing

Contributions are welcome! This package is designed to be general-purpose and framework-agnostic. When adding new features, please ensure:

1. **No framework dependencies** in core tools (keep them as plain async functions)
2. **No hardcoded institution-specific values** (use environment variables)
3. **Concise, LLM-friendly output** formatting
4. **Comprehensive error handling** (return error strings, don't raise exceptions)
5. **Documentation and tests** for all new features
6. **Framework adapters** in separate `adapters/` module

### Adding New Framework Adapters

To add support for a new LLM framework:

1. Create `library_tools/adapters/your_framework.py`
2. Import the core tool functions
3. Wrap them in your framework's decorator/pattern
4. Add optional dependency to `pyproject.toml`
5. Document usage in README

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/zweibels/library-tools/issues
- Repository: https://github.com/zweibels/library-tools
