"""Unit tests for validation that do not require a live Neo4j instance."""
import pytest
from app import RouteApp


def test_rejects_invalid_route_metric():
    # Bypass __init__: this validation test does not need a live database.
    app = object.__new__(RouteApp)
    with pytest.raises(ValueError, match="metric"):
        app.ranked_routes("B01", "B10", metric="fastest-ish")


def test_rejects_invalid_hop_limit():
    app = object.__new__(RouteApp)
    with pytest.raises(ValueError, match="max_hops"):
        app.ranked_routes("B01", "B10", max_hops=99)


def test_rejects_invalid_shortest_route_hop_limit():
    app = object.__new__(RouteApp)
    with pytest.raises(ValueError, match="max_hops"):
        app.shortest_hop_route("B01", "B10", max_hops=0)
