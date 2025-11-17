"""
Comprehensive tests for institution-filtered holdings.

Tests that check_institutions parameter correctly filters holdings results
and compares them to full holdings to ensure accuracy.
"""

import pytest
from library_tools.worldcat.tools import lookup_worldcat_isbn


# Use a well-known book with many holdings
TEST_ISBN = "978-0-14-303943-3"  # The Grapes of Wrath by Steinbeck
TEST_INSTITUTIONS = ["NYP", "DLC", "HUH"]  # New York Public, Library of Congress, Harvard


@pytest.mark.asyncio
async def test_single_institution_filter():
    """Test 1: Filter by a single institution and verify result."""
    # Get full holdings
    full_result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        holdings_limit=500  # Get enough to include our test institution
    )

    # Get filtered holdings for just NYP
    filtered_result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        check_institutions=["NYP"]
    )

    # Parse results
    assert "Total Holdings:" in full_result
    assert "Total Holdings:" in filtered_result

    # Extract total counts - should be the same
    full_total = int(full_result.split("Total Holdings:")[1].split()[0])
    filtered_total = int(filtered_result.split("Total Holdings:")[1].split()[0])
    assert full_total == filtered_total, "Total holdings count should be the same regardless of filter"

    # Check if NYP appears in results
    if "Available at:" in filtered_result:
        institutions = filtered_result.split("Available at:")[1].split("\n")[0]
        # Should have at most 1 institution
        inst_list = [i.strip() for i in institutions.split(",") if i.strip()]
        assert len(inst_list) <= 1, f"Should have at most 1 institution, got {len(inst_list)}"
        if inst_list:
            assert "NYP" in inst_list[0], "Returned institution should be NYP"
            # Verify NYP is in full holdings
            full_institutions = full_result.split("Available at:")[1].split("\n")[0]
            assert "NYP" in full_institutions, "NYP should be in full holdings if returned in filtered"


@pytest.mark.asyncio
async def test_multiple_institutions_filter():
    """Test 2: Filter by multiple institutions and verify each."""
    # Get full holdings
    full_result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        holdings_limit=500
    )

    # Get filtered holdings for 3 institutions
    filtered_result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        check_institutions=TEST_INSTITUTIONS
    )

    # Both should have same total
    full_total = int(full_result.split("Total Holdings:")[1].split()[0])
    filtered_total = int(filtered_result.split("Total Holdings:")[1].split()[0])
    assert full_total == filtered_total

    if "Available at:" in filtered_result:
        filtered_inst_str = filtered_result.split("Available at:")[1].split("\n")[0]
        filtered_institutions = [i.strip() for i in filtered_inst_str.split(",") if i.strip()]

        # All returned institutions should be from our filter list
        for inst in filtered_institutions:
            assert any(test_inst in inst for test_inst in TEST_INSTITUTIONS), \
                f"Institution {inst} should be in test institutions list"

        # Each returned institution should be in full holdings
        full_inst_str = full_result.split("Available at:")[1].split("\n")[0]
        for inst in filtered_institutions:
            assert inst in full_inst_str, f"{inst} should be in full holdings"


@pytest.mark.asyncio
async def test_total_holdings_consistency():
    """Test 3: Verify total_holdings is consistent across all filtering modes."""
    # Get results with different filters
    no_filter = await lookup_worldcat_isbn(isbn=TEST_ISBN, fetch_holdings=True, holdings_limit=10)
    with_filter = await lookup_worldcat_isbn(isbn=TEST_ISBN, fetch_holdings=True, check_institutions=["NYP"])
    limited_filter = await lookup_worldcat_isbn(isbn=TEST_ISBN, fetch_holdings=True, holdings_limit=5)

    # Extract totals from all three
    totals = []
    for result in [no_filter, with_filter, limited_filter]:
        if "Total Holdings:" in result:
            total = int(result.split("Total Holdings:")[1].split()[0])
            totals.append(total)

    # All totals should be identical
    assert len(set(totals)) == 1, f"All total holdings should be the same, got {totals}"


@pytest.mark.asyncio
async def test_institution_not_holding():
    """Test 4: Filter by institution that doesn't have the item."""
    # Use an unlikely institution code
    result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        check_institutions=["FAKE123"]
    )

    # Should still have total holdings
    assert "Total Holdings:" in result
    total = int(result.split("Total Holdings:")[1].split()[0])
    assert total > 0, "Should still report global total holdings"

    # But shouldn't have any institutions listed, or the available line shouldn't appear
    if "Available at:" in result:
        inst_str = result.split("Available at:")[1].split("\n")[0].strip()
        # Should be empty or just have FAKE123 if it somehow exists
        if inst_str:
            assert "FAKE123" in inst_str


@pytest.mark.asyncio
async def test_comparison_filtered_vs_full():
    """Test 5: Get full holdings and verify filtered results are subset."""
    # Get full holdings (limit to 500 for practical reasons)
    full_result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        holdings_limit=500
    )

    # Extract institutions from full result
    if "Available at:" not in full_result:
        pytest.skip("No holdings data available")

    full_inst_str = full_result.split("Available at:")[1].split("\n")[0]
    full_institutions = [i.strip() for i in full_inst_str.split(",") if i.strip()]

    # Pick 5 random institutions from the full list
    import random
    test_sample = random.sample(full_institutions, min(5, len(full_institutions)))

    # Get filtered results for those 5
    filtered_result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        check_institutions=test_sample
    )

    # Should have holdings for all 5
    if "Available at:" in filtered_result:
        filtered_inst_str = filtered_result.split("Available at:")[1].split("\n")[0]
        filtered_institutions = [i.strip() for i in filtered_inst_str.split(",") if i.strip()]

        # Each institution in our sample should appear in filtered results
        for inst in test_sample:
            assert inst in filtered_institutions, f"{inst} should be in filtered results"

        # Should have exactly those institutions (or fewer if some don't have it)
        for inst in filtered_institutions:
            assert inst in test_sample, f"{inst} should only be from our test sample"


@pytest.mark.asyncio
async def test_empty_list_raises_error():
    """Test 6: Empty list should return a clear validation error message."""
    result = await lookup_worldcat_isbn(
        isbn=TEST_ISBN,
        fetch_holdings=True,
        check_institutions=[]
    )

    # Should return an error message (tools format errors as strings)
    assert "Invalid input" in result or "check_institutions cannot be empty" in result
    assert "Use None" in result or "fetch all holdings" in result
