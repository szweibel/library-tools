# Library Tools Examples

This directory contains practical examples demonstrating how to use the library-tools package.

## Prerequisites

Before running these examples:

1. **Install the package**:
   ```bash
   cd /path/to/library-tools
   poetry install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **Activate environment**:
   ```bash
   poetry shell
   ```

## Examples

### 1. Basic Search (`basic_search.py`)

**What it demonstrates:**
- Simple catalog searches using Primo
- Finding academic papers with OpenAlex
- Searching by different fields (title, subject, etc.)

**Run it:**
```bash
python examples/basic_search.py
```

**Use this when:**
- You're new to the package
- You want to understand basic usage
- You need simple search examples

---

### 2. Multi-Tool Workflow (`multi_tool.py`)

**What it demonstrates:**
- Using multiple tools together
- Complete research workflow for a topic
- Author-focused research

**Run it:**
```bash
python examples/multi_tool.py
```

**Use this when:**
- You need comprehensive research workflows
- You want to combine multiple data sources
- You're building research assistant features

**Key features:**
- Topic research workflow (guides → databases → catalog → papers → repository)
- Author research workflow (find author → their papers → library holdings)

---

### 3. Agent Integration (`agent_integration.py`)

**What it demonstrates:**
- Integration with Claude Agent SDK
- How Claude uses tools automatically
- Multi-turn conversations with tool use

**Run it:**
```bash
# Requires ANTHROPIC_API_KEY in environment
export ANTHROPIC_API_KEY=your_key_here
python examples/agent_integration.py
```

**Use this when:**
- Building chatbots or agents
- Implementing conversational interfaces
- Want Claude to decide which tools to use

**Key features:**
- Natural language queries
- Automatic tool selection
- Complex multi-tool workflows

---

### 4. Direct Client Usage (`direct_client.py`)

**What it demonstrates:**
- Using API clients directly (not tool wrappers)
- Accessing full Pydantic models
- Custom integrations

**Run it:**
```bash
python examples/direct_client.py
```

**Use this when:**
- Building non-LLM applications
- Need more control over API calls
- Want to create custom formatters
- Integrating into existing systems

**Benefits:**
- Type-safe with Pydantic models
- Full access to all response data
- No LLM formatting overhead
- Easier to test and debug

---

## Configuration Examples

### Minimal OpenAlex Setup
```env
# OpenAlex works without credentials!
OPENALEX_EMAIL=your.email@institution.edu  # Optional but recommended
```

### Full Setup
```env
# Primo
PRIMO_API_KEY=your_key
PRIMO_VID=01YOURSCHOOL:VIEW

# OpenAlex
OPENALEX_EMAIL=your.email@institution.edu

# LibGuides
LIBGUIDES_SITE_ID=12345
LIBGUIDES_CLIENT_ID=your_client_id
LIBGUIDES_CLIENT_SECRET=your_secret

# Repository
REPOSITORY_BASE_URL=https://content-out.bepress.com/v2/your-institution.edu
REPOSITORY_API_KEY=your_key

# Claude (for agent_integration.py)
ANTHROPIC_API_KEY=your_anthropic_key
```

## Quick Start

**Try OpenAlex first** (no credentials needed):
```bash
# Just set your email (optional but recommended)
echo "OPENALEX_EMAIL=your@email.com" > .env

# Run the basic example
python examples/basic_search.py
```

## Common Issues

### "Configuration error: X not configured"
**Solution:** Configure the required environment variable in your `.env` file.

### "Module not found: library_tools"
**Solution:** Install the package first:
```bash
poetry install
```

### "No results found"
**Solution:**
- Check your API credentials are correct
- Try broader search terms
- Verify you have access to the service

### AsyncIO errors
**Solution:** Make sure you're using Python 3.10+:
```bash
python --version  # Should be 3.10 or higher
```

## Modifying Examples

All examples are simple Python scripts that you can easily modify:

1. **Change search queries**: Edit the query strings
2. **Adjust limits**: Change `limit` parameters
3. **Add filters**: Use additional parameters (year, field, etc.)
4. **Combine differently**: Mix and match tools for your workflow

## Next Steps

After trying these examples:

1. Read the [main README](../README.md) for full API documentation
2. Check the [tests](../tests/) for more usage patterns
3. Build your own tools using these as templates
4. Contribute your examples back to the project!

## Support

- **Issues**: https://github.com/yourusername/library-tools/issues
- **Documentation**: https://library-tools.readthedocs.io
- **Discussions**: https://github.com/yourusername/library-tools/discussions
