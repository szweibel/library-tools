#!/usr/bin/env python3
"""WorldCat example: ISBN lookup, book search, and classification."""

import asyncio
from library_tools.worldcat.tools import (
    lookup_worldcat_isbn,
    search_worldcat_books,
    get_worldcat_classification,
    get_worldcat_full_record,
)


async def isbn_lookup():
    """Example: Look up a book by ISBN."""
    print("=" * 60)
    print("EXAMPLE 1: Look Up Book by ISBN")
    print("=" * 60)

    isbn = "9780451524935"  # 1984 by George Orwell
    print(f"\nLooking up ISBN: {isbn}...")

    try:
        result = await lookup_worldcat_isbn(isbn=isbn)
        print(result)
    except Exception as e:
        print(f"Error: {e}")


async def doi_to_isbn():
    """Example: Find ISBN using DOI."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Find ISBN from DOI")
    print("=" * 60)

    doi = "10.1093/oso/9780190672454.001.0001"
    print(f"\nSearching for book with DOI: {doi}...")

    try:
        result = await lookup_worldcat_isbn(doi=doi)
        print(result)
    except Exception as e:
        print(f"Error: {e}")


async def title_author_search():
    """Example: Find book by title and author."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Find Book by Title and Author")
    print("=" * 60)

    title = "The Great Gatsby"
    author = "Fitzgerald"
    print(f"\nSearching for: {title} by {author}...")

    try:
        result = await lookup_worldcat_isbn(title=title, author=author)
        print(result)

        # Note: This returns OCLC number which can be used for follow-up queries
    except Exception as e:
        print(f"Error: {e}")


async def keyword_search():
    """Example: Search for books by keyword."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Search Books by Keyword")
    print("=" * 60)

    query = "digital humanities"
    print(f"\nSearching WorldCat for: {query}...")

    try:
        result = await search_worldcat_books(
            query=query,
            year_from=2015,
            year_to=2024,
            limit=10
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}")


async def language_search():
    """Example: Search for books in a specific language."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Search by Language")
    print("=" * 60)

    query = "inteligencia artificial"
    language = "spa"  # Spanish
    print(f"\nSearching for Spanish books about: {query}...")

    try:
        result = await search_worldcat_books(
            query=query,
            language=language,
            limit=5
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}")


async def get_classification():
    """Example: Get LC and Dewey classification."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Get Classification")
    print("=" * 60)

    oclc_number = "1"  # Bible (Genesis) - a well-known record
    print(f"\nGetting classification for OCLC: {oclc_number}...")

    try:
        result = await get_worldcat_classification(oclc_number=oclc_number)
        print(result)
    except Exception as e:
        print(f"Error: {e}")


async def full_bibliographic_record():
    """Example: Get complete bibliographic record with subjects."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Get Full Bibliographic Record")
    print("=" * 60)

    oclc_number = "1"
    print(f"\nGetting full record for OCLC: {oclc_number}...")

    try:
        result = await get_worldcat_full_record(oclc_number=oclc_number)
        print(result)
    except Exception as e:
        print(f"Error: {e}")


async def workflow_example():
    """Example: Complete workflow - search, then get details."""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Complete Workflow")
    print("=" * 60)

    print("\nStep 1: Search for books...")
    try:
        search_results = await search_worldcat_books(
            query="critical pedagogy",
            year_from=2020,
            limit=3
        )
        print(search_results)

        # In practice, you would parse the OCLC number from results
        # and use it for follow-up queries like:
        # - get_worldcat_classification(oclc_number)
        # - get_worldcat_full_record(oclc_number)

        print("\nStep 2: Extract OCLC numbers from results (see above)")
        print("Step 3: Use OCLC numbers with classification/full record tools")

    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all WorldCat examples."""

    # Basic lookups
    await isbn_lookup()
    await doi_to_isbn()
    await title_author_search()

    # Searching
    await keyword_search()
    await language_search()

    # Getting details
    await get_classification()
    await full_bibliographic_record()

    # Complete workflow
    await workflow_example()

    print("\n" + "=" * 60)
    print("WorldCat Tools Summary")
    print("=" * 60)
    print("\nAvailable WorldCat tools:")
    print("  • lookup_worldcat_isbn() - Find books by ISBN, DOI, or title/author")
    print("  • search_worldcat_books() - Search by keyword with filters")
    print("  • get_worldcat_classification() - Get LC/Dewey classification")
    print("  • get_worldcat_full_record() - Get complete metadata with subjects")


if __name__ == "__main__":
    print("\n🌐 Library Tools - WorldCat Examples\n")
    print("This example demonstrates:")
    print("  1. ISBN and DOI lookups")
    print("  2. Title/author searches")
    print("  3. Keyword searches with filters")
    print("  4. Language filtering")
    print("  5. Classification lookups")
    print("  6. Full bibliographic records")
    print("  7. Complete workflows")
    print("\nNote: Requires OCLC credentials in .env\n")

    asyncio.run(main())
