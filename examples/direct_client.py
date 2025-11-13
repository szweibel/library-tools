#!/usr/bin/env python3
"""Example: Using clients directly without tool wrappers."""

import asyncio
from library_tools.primo.client import PrimoClient
from library_tools.openalex.client import OpenAlexClient
from library_tools.libguides.client import LibGuidesClient
from library_tools.repository.client import RepositoryClient


async def primo_example():
    """Direct usage of PrimoClient."""
    print("\n" + "=" * 80)
    print("PRIMO CLIENT EXAMPLE")
    print("=" * 80)

    try:
        # Initialize client
        client = PrimoClient(
            api_key="your_api_key",
            vid="01YOUR:VIEW",
            scope="Everything"
        )

        # Search catalog
        results = await client.search(
            query="Python programming",
            field="title",
            operator="contains",
            limit=5
        )

        print(f"\nFound {results.total} results")
        for i, doc in enumerate(results.documents, 1):
            print(f"\n{i}. {doc.title}")
            if doc.authors:
                print(f"   Authors: {', '.join(doc.authors[:3])}")
            if doc.publication_year:
                print(f"   Year: {doc.publication_year}")
            if doc.permalink:
                print(f"   URL: {doc.permalink}")

    except Exception as e:
        print(f"Error: {e}")


async def openalex_example():
    """Direct usage of OpenAlexClient."""
    print("\n" + "=" * 80)
    print("OPENALEX CLIENT EXAMPLE")
    print("=" * 80)

    try:
        # Initialize client
        client = OpenAlexClient(email="your.email@institution.edu")

        # Search works
        print("\nSearching for works...")
        works = await client.search_works(
            query="neural networks",
            limit=5,
            year_from=2023,
            open_access_only=True
        )

        for i, work in enumerate(works, 1):
            print(f"\n{i}. {work.title} ({work.publication_year})")
            print(f"   Citations: {work.cited_by_count}")
            if work.journal:
                print(f"   Journal: {work.journal}")
            if work.doi:
                print(f"   DOI: {work.doi}")

        # Search authors
        print("\n\nSearching for authors...")
        authors = await client.search_authors(
            name="Andrew Ng",
            limit=3
        )

        for i, author in enumerate(authors, 1):
            print(f"\n{i}. {author.name}")
            print(f"   Publications: {author.works_count}")
            print(f"   Citations: {author.cited_by_count}")
            if author.h_index:
                print(f"   h-index: {author.h_index}")
            if author.institution:
                print(f"   Institution: {author.institution}")

    except Exception as e:
        print(f"Error: {e}")


async def libguides_example():
    """Direct usage of LibGuidesClient."""
    print("\n" + "=" * 80)
    print("LIBGUIDES CLIENT EXAMPLE")
    print("=" * 80)

    try:
        # Initialize client
        client = LibGuidesClient(
            site_id="12345",
            client_id="your_client_id",
            client_secret="your_client_secret"
        )

        # Search databases
        print("\nSearching databases...")
        db_results = await client.search_databases(
            search="psychology",
            limit=5
        )

        print(f"Found {db_results.total} databases")
        for i, db in enumerate(db_results.databases, 1):
            print(f"\n{i}. {db.name}")
            if db.description:
                print(f"   {db.description[:100]}...")
            if db.subjects:
                print(f"   Subjects: {', '.join(db.subjects)}")
            if db.url:
                print(f"   URL: {db.url}")

        # Search guides
        print("\n\nSearching guides...")
        guide_results = await client.search_guides(
            search="research methods",
            limit=3
        )

        print(f"Found {guide_results.total} guides")
        for i, guide in enumerate(guide_results.guides, 1):
            print(f"\n{i}. {guide.name}")
            if guide.description:
                print(f"   {guide.description[:100]}...")
            if guide.owner_name:
                print(f"   By: {guide.owner_name}")
            if guide.pages:
                print(f"   Pages: {len(guide.pages)}")

    except Exception as e:
        print(f"Error: {e}")


async def repository_example():
    """Direct usage of RepositoryClient."""
    print("\n" + "=" * 80)
    print("REPOSITORY CLIENT EXAMPLE")
    print("=" * 80)

    try:
        # Initialize client
        client = RepositoryClient(
            base_url="https://content-out.bepress.com/v2/institution.edu",
            api_key="your_api_key"
        )

        # Search repository
        print("\nSearching repository...")
        results = await client.search(
            query="machine learning",
            limit=5
        )

        print(f"Found {results.total} works")
        for i, work in enumerate(results.works, 1):
            print(f"\n{i}. {work.title}")
            if work.authors:
                print(f"   Authors: {', '.join(work.authors[:3])}")
            if work.publication_year:
                print(f"   Year: {work.publication_year}")
            if work.document_type:
                print(f"   Type: {work.document_type}")
            if work.url:
                print(f"   URL: {work.url}")

        # Get latest works
        print("\n\nGetting latest works...")
        latest = await client.get_latest_works(limit=3)

        for i, work in enumerate(latest.works, 1):
            print(f"\n{i}. {work.title}")
            print(f"   Year: {work.publication_year}")

    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all client examples."""
    print("\n🔧 Library Tools - Direct Client Usage Examples\n")
    print("This example shows how to use the API clients directly")
    print("instead of the LLM tool wrappers.\n")
    print("Use cases:")
    print("  • Custom integrations")
    print("  • Non-LLM applications")
    print("  • Direct API access with more control")
    print("  • Building your own tool wrappers\n")

    # Note: These examples will fail without proper credentials
    # Comment out examples for services you haven't configured

    await openalex_example()  # No credentials needed!

    # Uncomment these after configuring your .env file:
    # await primo_example()
    # await libguides_example()
    # await repository_example()

    print("\n" + "=" * 80)
    print("✅ EXAMPLES COMPLETE")
    print("=" * 80)
    print("\nBenefits of direct client usage:")
    print("  • Access to full Pydantic models (type-safe)")
    print("  • More control over parameters")
    print("  • Can build custom formatters")
    print("  • Easier to integrate into non-LLM workflows")


if __name__ == "__main__":
    asyncio.run(main())
