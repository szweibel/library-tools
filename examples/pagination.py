#!/usr/bin/env python3
"""Pagination example: Retrieve multiple pages of search results."""

import asyncio
from library_tools.openalex.tools import search_works
from library_tools.repository.tools import search_repository
from library_tools.worldcat.tools import search_worldcat_books


async def openalex_pagination():
    """Example: Get multiple pages from OpenAlex (page-based pagination)."""
    print("=" * 60)
    print("OpenAlex Pagination (page-based)")
    print("=" * 60)

    query = "climate change"
    pages_to_fetch = 3
    results_per_page = 10

    print(f"\nFetching {pages_to_fetch} pages of results for '{query}'")
    print(f"Results per page: {results_per_page}\n")

    all_results = []
    for page in range(1, pages_to_fetch + 1):
        print(f"Fetching page {page}...")
        try:
            result = await search_works(
                query=query,
                limit=results_per_page,
                page=page,
                year_from=2020
            )
            all_results.append(result)
            print(f"✓ Page {page} retrieved")
        except Exception as e:
            print(f"✗ Error on page {page}: {e}")

    print(f"\nTotal pages retrieved: {len(all_results)}")
    print(f"Estimated total results: {len(all_results) * results_per_page}")


async def repository_pagination():
    """Example: Get multiple pages from repository (offset-based pagination)."""
    print("\n" + "=" * 60)
    print("Repository Pagination (offset-based, starts at 0)")
    print("=" * 60)

    collection = "gc_etds"
    results_per_page = 20
    pages_to_fetch = 3

    print(f"\nFetching {pages_to_fetch} pages from collection '{collection}'")
    print(f"Results per page: {results_per_page}\n")

    all_results = []
    for page_num in range(pages_to_fetch):
        offset = page_num * results_per_page
        print(f"Fetching page {page_num + 1} (offset={offset})...")
        try:
            result = await search_repository(
                collection=collection,
                limit=results_per_page,
                start=offset
            )
            all_results.append(result)
            print(f"✓ Page {page_num + 1} retrieved")
        except Exception as e:
            print(f"✗ Error on page {page_num + 1}: {e}")

    print(f"\nTotal pages retrieved: {len(all_results)}")


async def worldcat_pagination():
    """Example: Get multiple pages from WorldCat (offset-based, starts at 1)."""
    print("\n" + "=" * 60)
    print("WorldCat Pagination (offset-based, starts at 1)")
    print("=" * 60)

    query = "python programming"
    results_per_page = 10
    pages_to_fetch = 3

    print(f"\nFetching {pages_to_fetch} pages for '{query}'")
    print(f"Results per page: {results_per_page}\n")

    all_results = []
    for page_num in range(pages_to_fetch):
        # WorldCat offset is 1-based: page 1 = offset 1, page 2 = offset 11, etc.
        offset = (page_num * results_per_page) + 1
        print(f"Fetching page {page_num + 1} (offset={offset})...")
        try:
            result = await search_worldcat_books(
                query=query,
                limit=results_per_page,
                offset=offset
            )
            all_results.append(result)
            print(f"✓ Page {page_num + 1} retrieved")
        except Exception as e:
            print(f"✗ Error on page {page_num + 1}: {e}")

    print(f"\nTotal pages retrieved: {len(all_results)}")


async def main():
    """Run all pagination examples."""

    # OpenAlex (page-based)
    await openalex_pagination()

    # Repository (0-based offset)
    try:
        await repository_pagination()
    except Exception as e:
        print(f"\nRepository example skipped: {e}")

    # WorldCat (1-based offset)
    try:
        await worldcat_pagination()
    except Exception as e:
        print(f"\nWorldCat example skipped: {e}")

    print("\n" + "=" * 60)
    print("Pagination Summary")
    print("=" * 60)
    print("\nDifferent services use different pagination styles:")
    print("  • OpenAlex: page parameter (1, 2, 3, ...)")
    print("  • Primo & Repository: start parameter (0, 100, 200, ...)")
    print("  • WorldCat: offset parameter (1, 51, 101, ...)")


if __name__ == "__main__":
    print("\n📄 Library Tools - Pagination Examples\n")
    print("This example demonstrates:")
    print("  1. Page-based pagination (OpenAlex)")
    print("  2. 0-based offset pagination (Repository)")
    print("  3. 1-based offset pagination (WorldCat)")
    print("\nNote: Configure .env with appropriate credentials.\n")

    asyncio.run(main())
