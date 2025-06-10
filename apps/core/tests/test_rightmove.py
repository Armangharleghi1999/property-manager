import pytest
import requests
from unittest.mock import patch, MagicMock
from apps.core.adapters.rightmove import RightmoveAdapter


@pytest.mark.parametrize(
    "url",
    [
        "https://www.rightmove.co.uk/property-for-sale/example-1",
        "https://www.rightmove.co.uk/property-for-sale/example-2",
    ],
)
@patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
def test_fetch_returns_expected_keys(mock_get, url):
    """Test that fetch returns the expected keys."""
    mock_response = MagicMock()
    mock_response.text = '<html><script type=\'application/ld+json\'>{"@type": "Offer", "itemOffered": {"address": {"streetAddress": "123 Example St"}}, "price": 1000000}</script></html>'
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    data = RightmoveAdapter.fetch(url)
    assert set(data.keys()) == {"url", "address", "price", "service_charge"}
    assert data["url"] == url


@patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
def test_fetch_raises_http_error(mock_get):
    """Test that fetch raises an HTTPError for bad responses."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        RightmoveAdapter.fetch("https://www.rightmove.co.uk/property-for-sale/example")


@patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
def test_fetch_handles_no_json_ld(mock_get):
    """Test that fetch handles cases where no JSON-LD scripts are found."""
    mock_response = MagicMock()
    mock_response.text = "<html></html>"
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="PAGE_MODEL JSON extraction failed"):
        RightmoveAdapter.fetch("https://www.rightmove.co.uk/property-for-sale/example")


@patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
def test_fetch_parses_next_data(mock_get):
    """Test that fetch correctly parses Next.js __NEXT_DATA__ fallback."""
    mock_response = MagicMock()
    mock_response.text = '<html><script id=\'__NEXT_DATA__\' type=\'application/json\'>{"props": {"pageProps": {"initialReduxState": {"propertySummary": {"listing": {"displayAddress": "123 Example St", "formattedPrice": "£1,000,000"}}, "propertyDescription": {"description": "A beautiful property"}}}}</script></html>'
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    data = RightmoveAdapter.fetch(
        "https://www.rightmove.co.uk/property-for-sale/example"
    )
    assert data["address"] == "123 Example St"
    assert data["price"] == "£1,000,000"
    assert data["summary"] == "A beautiful property"


@patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
def test_fetch_html_fallback(mock_get):
    """Test that fetch correctly parses HTML fallback."""
    mock_response = MagicMock()
    mock_response.text = "<html><h1>123 Example St</h1><p>Price: £1,000,000</p><p>Service charge: £200</p></html>"
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    data = RightmoveAdapter.fetch(
        "https://www.rightmove.co.uk/property-for-sale/example"
    )
    assert data["address"] == "123 Example St"
    assert data["price"] == "£1,000,000"
    assert data["service_charge"] == "£200"


@patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
def test_fetch_all_strategies_fail(mock_get):
    """Test that fetch raises ValueError when all parsing strategies fail."""
    mock_response = MagicMock()
    mock_response.text = "<html></html>"
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="PAGE_MODEL JSON extraction failed"):
        RightmoveAdapter.fetch("https://www.rightmove.co.uk/property-for-sale/example")
