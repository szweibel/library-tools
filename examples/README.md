# Examples

Practical examples showing how to use the library tools.

## Setup

1. Install the package:
   ```bash
   cd library-tools
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

2. Configure credentials in `.env` (copy from `.env.example`)

3. Run an example:
   ```bash
   python examples/basic_search.py
   ```

## Available Examples

### basic_search.py

Basic searches with Primo and OpenAlex.

```bash
python examples/basic_search.py
```

Shows:
- Searching library catalog
- Finding academic papers
- Searching by specific fields

Requires: `PRIMO_API_KEY`, `PRIMO_VID`, `OPENALEX_EMAIL` (optional)

---

### worldcat_lookup.py

WorldCat ISBN lookup, book search, and classification.

```bash
python examples/worldcat_lookup.py
```

Shows:
- ISBN and DOI lookups
- Title/author searches
- Keyword searches with year and language filters
- LC and Dewey classification
- Full bibliographic records
- Complete workflow example

Requires: `OCLC_CLIENT_ID`, `OCLC_CLIENT_SECRET`

---

### pagination.py

Retrieving multiple pages of results.

```bash
python examples/pagination.py
```

Shows:
- Page-based pagination (OpenAlex)
- 0-based offset pagination (Repository)
- 1-based offset pagination (WorldCat)

Requires: Credentials for the services you want to test

---

### multi_tool.py

Using multiple tools together for research workflows.

```bash
python examples/multi_tool.py
```

Shows:
- Topic research workflow
- Author research workflow
- Combining multiple data sources

Requires: Multiple service credentials

---

### agent_integration.py

Integration with Claude Agent SDK for conversational search.

```bash
python examples/agent_integration.py
```

Shows:
- Natural language queries
- Automatic tool selection
- Multi-turn conversations

**With Claude Code installed:** The Claude Agent SDK uses Claude Code's authentication automatically

**Without Claude Code:** Set `ANTHROPIC_API_KEY` environment variable

Also requires: Credentials for library services you want to use

---

### direct_client.py

Using API clients directly (without tool wrappers).

```bash
python examples/direct_client.py
```

Shows:
- Using clients instead of tools
- Working with Pydantic models
- Custom formatting

Useful for:
- Non-LLM applications
- Custom integrations
- More control over API calls

---

## Quick Start

Try OpenAlex first (no credentials required):

```bash
echo "OPENALEX_EMAIL=your@email.com" > .env
python examples/basic_search.py
```

## Common Issues

**"Configuration error"** - Add required credentials to `.env`

**"Module not found"** - Install the package: `uv pip install -e .`

**"No results"** - Check credentials or try broader search terms

**AsyncIO errors** - Use Python 3.10 or higher

## Modifying Examples

All examples are simple Python scripts. Modify them by:
- Changing query strings
- Adjusting limit parameters
- Adding filters (year, field, language)
- Combining tools differently

## Configuration Reference

Minimal (OpenAlex only):
```bash
OPENALEX_EMAIL=your@email.com
```

Complete:
```bash
# Primo
PRIMO_API_KEY=your_key
PRIMO_VID=01INST:VIEW

# OpenAlex
OPENALEX_EMAIL=your@email.com

# WorldCat
OCLC_CLIENT_ID=your_client_id
OCLC_CLIENT_SECRET=your_client_secret

# LibGuides
LIBGUIDES_SITE_ID=123
LIBGUIDES_CLIENT_ID=your_client_id
LIBGUIDES_CLIENT_SECRET=your_secret

# Repository
REPOSITORY_BASE_URL=https://content-out.bepress.com/v2/institution.edu
REPOSITORY_API_KEY=your_key

# Claude (for agent_integration.py, optional if Claude Code is installed)
# ANTHROPIC_API_KEY=your_key
```

**Note:** When Claude Code is installed, `ANTHROPIC_API_KEY` is not required - the Claude Agent SDK uses Claude Code's authentication automatically.
