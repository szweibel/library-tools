#!/usr/bin/env python3
"""Advanced example: Using multiple tools together for research assistance."""

import asyncio
from library_tools import (
    search_primo,
    search_works,
    search_authors,
    search_databases,
    search_guides,
    search_repository,
)


async def research_workflow(topic: str):
    """Complete research workflow for a given topic."""
    print("=" * 80)
    print(f"RESEARCH WORKFLOW: {topic}")
    print("=" * 80)

    # Step 1: Find research guides
    print("\n📚 Step 1: Finding research guides...")
    try:
        guides = await search_guides(search=topic, limit=3)
        print(guides)
    except Exception as e:
        print(f"Could not search guides: {e}")

    # Step 2: Find relevant databases
    print("\n💾 Step 2: Finding relevant databases...")
    try:
        databases = await search_databases(search=topic, limit=5)
        print(databases)
    except Exception as e:
        print(f"Could not search databases: {e}")

    # Step 3: Search library catalog
    print("\n📖 Step 3: Searching library catalog for books...")
    try:
        books = await search_primo(
            query=topic,
            field="subject",
            limit=5
        )
        print(books)
    except Exception as e:
        print(f"Could not search catalog: {e}")

    # Step 4: Find recent academic research
    print("\n🔬 Step 4: Finding recent academic research...")
    try:
        papers = await search_works(
            query=topic,
            year_from=2022,
            limit=5
        )
        print(papers)
    except Exception as e:
        print(f"Could not search academic papers: {e}")

    # Step 5: Check institutional repository
    print("\n🎓 Step 5: Checking institutional repository...")
    try:
        theses = await search_repository(
            query=topic,
            limit=3
        )
        print(theses)
    except Exception as e:
        print(f"Could not search repository: {e}")


async def author_workflow(author_name: str):
    """Research workflow focused on a specific author."""
    print("\n" + "=" * 80)
    print(f"AUTHOR RESEARCH: {author_name}")
    print("=" * 80)

    # Find the author
    print(f"\n👤 Finding author '{author_name}'...")
    try:
        authors = await search_authors(name=author_name, limit=3)
        print(authors)

        # Note: In a real workflow, you would parse the author ID from the results
        # and use it to get their works:
        # author_id = parse_author_id(authors)
        # works = await get_author_works(author_id=author_id, limit=10)
    except Exception as e:
        print(f"Could not search authors: {e}")

    # Check if they're in the catalog
    print(f"\n📚 Checking library catalog for works by {author_name}...")
    try:
        catalog = await search_primo(
            query=author_name,
            field="creator",
            limit=5
        )
        print(catalog)
    except Exception as e:
        print(f"Could not search catalog: {e}")


async def main():
    """Run multi-tool examples."""
    # Example 1: Complete research workflow on a topic
    await research_workflow("climate change")

    # Example 2: Author-focused research
    await author_workflow("Noam Chomsky")

    print("\n" + "=" * 80)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 80)
    print("\nThis example demonstrated:")
    print("  • Finding research guides for a topic")
    print("  • Discovering relevant databases")
    print("  • Searching the library catalog")
    print("  • Finding academic publications")
    print("  • Checking the institutional repository")
    print("  • Researching a specific author")


if __name__ == "__main__":
    print("\n🔧 Library Tools - Multi-Tool Research Workflow\n")
    print("This example shows how to combine multiple tools for comprehensive research.\n")
    print("Note: Configure your .env file with credentials for the tools you want to use.")
    print("      Tools will gracefully handle missing configuration.\n")

    asyncio.run(main())
