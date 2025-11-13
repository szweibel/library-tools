# Getting Started with Library Tools

Quick guide to get up and running with library-tools.

## Installation

### Option 1: Development Installation (Recommended)

```bash
cd /Users/stephenzweibel/Apps/library-tools
poetry install
```

### Option 2: From PyPI (when published)

```bash
pip install library-tools
```

## Initial Setup

### 1. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials. **Minimum setup for testing:**

```env
# OpenAlex works without any credentials!
OPENALEX_EMAIL=your.email@institution.edu
```

### 2. Test Installation

Run a simple test:

```bash
poetry shell
python -c "from library_tools import search_works; print('✓ Installation successful!')"
```

## Quick Usage Examples

### Simple Search

```python
import asyncio
from library_tools import search_works

async def main():
    results = await search_works(
        query="machine learning",
        limit=5
    )
    print(results)

asyncio.run(main())
```

### With Claude Agent SDK

```python
from anthropic import Anthropic
from library_tools import search_works, search_primo

client = Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=[search_works, search_primo],
    messages=[{
        "role": "user",
        "content": "Find recent papers on climate change"
    }]
)
```

## Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=library_tools

# Specific test file
poetry run pytest tests/test_openalex.py

# Verbose output
poetry run pytest -v
```

## Running Examples

```bash
# Basic search example (OpenAlex - no credentials needed!)
python examples/basic_search.py

# Multi-tool workflow
python examples/multi_tool.py

# Direct client usage
python examples/direct_client.py

# Agent integration (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=your_key
python examples/agent_integration.py
```

## Available Tools

| Tool | Service | Requires Config? | Description |
|------|---------|------------------|-------------|
| `search_primo` | Primo | Yes | Search library catalog |
| `search_works` | OpenAlex | No | Find academic papers |
| `search_authors` | OpenAlex | No | Find researchers |
| `get_author_works` | OpenAlex | No | Get author's publications |
| `search_journals` | OpenAlex | No | Find academic journals |
| `search_databases` | LibGuides | Yes | Search database A-Z list |
| `search_guides` | LibGuides | Yes | Find research guides |
| `search_repository` | Repository | Yes | Search institutional repository |
| `get_latest_repository_works` | Repository | Yes | Get recent additions |
| `get_repository_work_details` | Repository | Yes | Get work details |

## Configuration Guide

### Primo (Ex Libris)

```env
PRIMO_API_KEY=your_api_key          # Required
PRIMO_VID=01YOURSCHOOL:VIEW         # Required
PRIMO_SCOPE=Everything               # Optional
```

**Get credentials:** Ex Libris Developer Network

### OpenAlex

```env
OPENALEX_EMAIL=your@email.com       # Optional (but recommended)
```

**Get credentials:** None needed! OpenAlex is free.

### LibGuides (SpringShare)

```env
LIBGUIDES_SITE_ID=12345             # Required
LIBGUIDES_CLIENT_ID=your_client     # Required
LIBGUIDES_CLIENT_SECRET=your_secret # Required
```

**Get credentials:** LibApps admin panel → API

### Repository (bePress/Digital Commons)

```env
REPOSITORY_BASE_URL=https://content-out.bepress.com/v2/institution.edu  # Required
REPOSITORY_API_KEY=your_api_key     # Required
```

**Get credentials:** Digital Commons admin panel

### Claude (for Agent SDK)

```env
ANTHROPIC_API_KEY=your_key          # Required for agent examples
```

**Get credentials:** https://console.anthropic.com

## Common Workflows

### Research Assistant Bot

```python
from anthropic import Anthropic
from library_tools import (
    search_primo,
    search_works,
    search_guides,
    search_databases
)

client = Anthropic()

# Claude automatically uses appropriate tools
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=[search_primo, search_works, search_guides, search_databases],
    messages=[{
        "role": "user",
        "content": "I'm researching renewable energy. What resources do we have?"
    }]
)
```

### Custom Integration

```python
from library_tools.openalex.client import OpenAlexClient

# Use client directly for custom formatting
client = OpenAlexClient(email="your@email.com")

works = await client.search_works(
    query="neural networks",
    year_from=2023,
    limit=10
)

# Works is a list of Pydantic models
for work in works:
    print(f"{work.title} - Citations: {work.cited_by_count}")
```

## Troubleshooting

### Import Errors

```bash
# Make sure package is installed
poetry install

# Activate environment
poetry shell
```

### Configuration Errors

```bash
# Check your .env file exists
ls -la .env

# Verify environment variables
python -c "from library_tools.common.config import get_settings; print(get_settings())"
```

### AsyncIO Errors

Make sure you're using Python 3.10+:

```bash
python --version
```

### API Errors

- **401/403**: Check your API credentials
- **404**: Verify the base URL is correct
- **429**: Rate limit - try adding a delay between requests

## Next Steps

1. **Read the examples**: See `examples/README.md`
2. **Check the tests**: Learn from `tests/`
3. **Read full docs**: See main `README.md`
4. **Build something**: Start with OpenAlex (no credentials needed!)

## Development

### Code Quality

```bash
# Format code
poetry run black library_tools tests examples

# Lint
poetry run ruff check library_tools

# Type check
poetry run mypy library_tools
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Support

- **Documentation**: See README.md and examples/
- **Issues**: GitHub Issues
- **Questions**: GitHub Discussions

## Quick Reference

### Import Everything

```python
from library_tools import (
    # Primo
    search_primo,
    # OpenAlex
    search_works,
    search_authors,
    get_author_works,
    search_journals,
    # LibGuides
    search_databases,
    search_guides,
    # Repository
    search_repository,
    get_latest_repository_works,
    get_repository_work_details,
)
```

### Test One Tool

```python
import asyncio
from library_tools import search_works

async def test():
    result = await search_works(query="test", limit=1)
    print(result)

asyncio.run(test())
```

That's it! You're ready to start using library-tools. 🚀
