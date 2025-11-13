#!/usr/bin/env python3
"""Basic example: Search library catalog and academic papers."""

import asyncio
from library_tools import search_primo, search_works


async def main():
    """Run basic searches."""
    print("=" * 60)
    print("EXAMPLE 1: Search Library Catalog")
    print("=" * 60)

    try:
        # Search for books about artificial intelligence
        print("\nSearching for 'artificial intelligence' in the library catalog...")
        catalog_results = await search_primo(
            query="artificial intelligence",
            field="any",
            limit=5
        )
        print(catalog_results)
    except Exception as e:
        print(f"Error searching catalog: {e}")

    print("\n" + "=" * 60)
    print("EXAMPLE 2: Search Academic Publications")
    print("=" * 60)

    try:
        # Search for recent open access papers
        print("\nSearching for recent open access papers on 'machine learning'...")
        academic_results = await search_works(
            query="machine learning",
            year_from=2023,
            open_access_only=True,
            limit=5
        )
        print(academic_results)
    except Exception as e:
        print(f"Error searching academic papers: {e}")

    print("\n" + "=" * 60)
    print("EXAMPLE 3: Search by Title")
    print("=" * 60)

    try:
        # Search for a specific book by title
        print("\nSearching for 'Introduction to Algorithms'...")
        title_results = await search_primo(
            query="Introduction to Algorithms",
            field="title",
            operator="contains",
            limit=3
        )
        print(title_results)
    except Exception as e:
        print(f"Error searching by title: {e}")


if __name__ == "__main__":
    print("\n🔍 Library Tools - Basic Search Examples\n")
    print("This example demonstrates:")
    print("  1. Searching a library catalog (Primo)")
    print("  2. Finding academic publications (OpenAlex)")
    print("  3. Searching by specific fields\n")
    print("Note: Make sure your .env file is configured with the appropriate credentials.\n")

    asyncio.run(main())
