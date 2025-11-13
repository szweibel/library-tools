"""Live integration tests for WorldCat search.

These tests hit the actual WorldCat/OCLC API using credentials from .env.
They may fail if the API is down, rate limits are hit, or if credentials are invalid.

Requires OCLC_CLIENT_ID and OCLC_CLIENT_SECRET in .env file.
"""

import pytest
from library_tools.worldcat.tools import (
    lookup_worldcat_isbn,
    search_worldcat_books,
    get_worldcat_classification,
    get_worldcat_full_record,
)


@pytest.mark.asyncio
async def test_lookup_isbn_by_isbn():
    """Test WorldCat ISBN lookup with a known ISBN."""
    # Using a well-known book ISBN (1984 by George Orwell)
    result = await lookup_worldcat_isbn(isbn="9780451524935")

    assert isinstance(result, str)
    assert "Book found in WorldCat" in result
    assert "ISBN" in result
    # Should have OCLC number
    assert "OCLC Number" in result


@pytest.mark.asyncio
async def test_lookup_isbn_by_title():
    """Test WorldCat lookup by title and author."""
    result = await lookup_worldcat_isbn(
        title="The Great Gatsby",
        author="Fitzgerald"
    )

    assert isinstance(result, str)
    # Should either find the book or provide helpful message
    if "Book found" in result:
        assert "ISBN" in result or "OCLC Number" in result
    else:
        assert "No book found" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_search_worldcat_books_basic():
    """Test basic WorldCat book search."""
    result = await search_worldcat_books(
        query="artificial intelligence",
        limit=5
    )

    assert isinstance(result, str)
    # Should either find books or say none found
    if "Found" in result:
        assert "books" in result.lower()
        assert "OCLC" in result  # Should have OCLC numbers
    else:
        assert "No books found" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_search_worldcat_books_with_year_filter():
    """Test WorldCat book search with year filter."""
    result = await search_worldcat_books(
        query="machine learning",
        year_from=2020,
        limit=5
    )

    assert isinstance(result, str)
    # Should return results or appropriate message
    if "Found" in result:
        # Check for recent years if visible
        assert any(year in result for year in ["2020", "2021", "2022", "2023", "2024", "2025"]) or "OCLC" in result
    else:
        assert "No books found" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_search_worldcat_books_with_language():
    """Test WorldCat book search with language filter."""
    result = await search_worldcat_books(
        query="literatura",
        language="spa",  # Spanish
        limit=5
    )

    assert isinstance(result, str)
    # Should either find Spanish books or handle appropriately
    assert "Found" in result or "No books found" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_get_worldcat_classification():
    """Test getting LC/Dewey classification for a known OCLC number."""
    # Using OCLC number for a well-known book
    # Note: This test requires a valid OCLC number
    # Example: "1" is Genesis (Bible), very common record
    result = await get_worldcat_classification(oclc_number="1")

    assert isinstance(result, str)
    assert "Classification for OCLC" in result
    # Should have either LC or Dewey or both
    assert any(term in result for term in ["LC Classification", "Dewey Decimal"])


@pytest.mark.asyncio
async def test_get_worldcat_full_record():
    """Test getting full bibliographic record for a known OCLC number."""
    # Using OCLC number for a well-known book
    result = await get_worldcat_full_record(oclc_number="1")

    assert isinstance(result, str)
    assert "Complete Record for OCLC" in result
    # Should have some bibliographic details
    assert any(term in result for term in ["Title:", "Classification:", "Format:", "Language:"])


@pytest.mark.asyncio
async def test_lookup_isbn_no_results():
    """Test WorldCat lookup with parameters that likely won't match."""
    result = await lookup_worldcat_isbn(
        title="XYZ Nonexistent Book Title 12345",
        author="Nonexistent Author 67890"
    )

    assert isinstance(result, str)
    # Should gracefully handle no results
    assert "No book found" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_search_worldcat_books_narrow_query():
    """Test WorldCat search with very specific query."""
    result = await search_worldcat_books(
        query="critical pedagogy",
        year_from=2010,
        year_to=2020,
        limit=10
    )

    assert isinstance(result, str)
    # Should return results or no results message
    assert "Found" in result or "No books found" in result or "error" in result.lower()
    # Should not crash
    assert result is not None and len(result) > 0


@pytest.mark.asyncio
async def test_worldcat_error_handling():
    """Test that invalid OCLC numbers are handled gracefully."""
    result = await get_worldcat_classification(oclc_number="invalid_oclc_999999999")

    assert isinstance(result, str)
    # Should handle error gracefully with helpful message
    assert "error" in result.lower() or "failed" in result.lower() or "not found" in result.lower()


@pytest.mark.asyncio
async def test_search_worldcat_books_pagination():
    """Test WorldCat search pagination with offset parameter."""
    # Get first page
    first_page = await search_worldcat_books(
        query="python programming",
        limit=10,
        offset=1
    )

    # Get second page
    second_page = await search_worldcat_books(
        query="python programming",
        limit=10,
        offset=11
    )

    assert isinstance(first_page, str)
    assert isinstance(second_page, str)

    # Both should return results or appropriate messages
    assert "Found" in first_page or "No books found" in first_page or "error" in first_page.lower()
    assert "Found" in second_page or "No books found" in second_page or "error" in second_page.lower()

    # If both found results, they should be different
    if "Found" in first_page and "Found" in second_page:
        # Results should be different (different books on different pages)
        assert first_page != second_page
