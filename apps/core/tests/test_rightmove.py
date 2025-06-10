import logging
import pytest
from apps.core.adapters.rightmove import RightmoveAdapter
import requests
import responses


# --- Unit tests for RightmoveAdapter ---
@pytest.mark.parametrize(
    "html,expected_address,expected_price",
    [
        (
            '<html><script type=\'application/ld+json\'>{"@type": "Offer", "itemOffered": {"address": {"streetAddress": "123 Example St"}}, "price": 1000000}</script></html>',
            "123 Example St",
            "£1000000",
        ),
    ],
)
def test_fetch_successful_json_ld_parsing(
    monkeypatch, html, expected_address, expected_price
):
    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["address"] == expected_address
    assert result["price"] == expected_price


def test_fetch_http_error(monkeypatch):
    def raise_http_error(*args, **kwargs):
        raise requests.HTTPError("HTTP Error")

    monkeypatch.setattr(RightmoveAdapter.session, "get", raise_http_error)
    with pytest.raises(requests.HTTPError):
        RightmoveAdapter.fetch("https://example.com")


def test_fetch_next_data_parsing(monkeypatch):
    html = (
        "<html><script id='__NEXT_DATA__' type='application/json'>"
        '{"props": {"pageProps": {"initialReduxState": {"propertySummary": {"listing": {"displayAddress": "123 Example St", "formattedPrice": "£1,000,000"}}, "propertyDescription": {"description": "A beautiful property"}}}}}'
        "</script></html>"
    )

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["address"] == "123 Example St"
    assert result["price"] == "£1,000,000"
    assert result["summary"] == "A beautiful property"


def test_fetch_html_fallback(monkeypatch):
    with open(
        r"apps/core/tests/test_samples/sample_rightmove_listing.html",
        encoding="utf-8",
    ) as f:
        html = f.read()

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert "address" in result
    assert "price" in result
    assert "service_charge" in result


def test_fetch_all_strategies_fail(monkeypatch):
    class MockResponse:
        status_code = 200
        text = "<html></html>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    with pytest.raises(ValueError):
        RightmoveAdapter.fetch("https://example.com")


def test_fetch_service_charge_parsing(monkeypatch):
    class MockResponse:
        status_code = 200
        text = "<html><p>Service charge: £300</p></html>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["service_charge"] == "£300"


def test_fetch_timeout(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout

    monkeypatch.setattr(RightmoveAdapter.session, "get", raise_timeout)
    with pytest.raises(requests.exceptions.Timeout):
        RightmoveAdapter.fetch("https://example.com")


def test_fetch_invalid_json_ld(monkeypatch):
    html = "<html><script type='application/ld+json'>Invalid JSON</script></html>"

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    with pytest.raises(ValueError):
        RightmoveAdapter.fetch("https://example.com")


def test_fetch_malformed_html(monkeypatch):
    html = "<html><h1>123 Example St"

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["address"] == "123 Example St"


def test_fetch_non_200_status_code(monkeypatch):
    class MockResponse:
        status_code = 404
        text = "Not Found"

        def raise_for_status(self):
            raise requests.HTTPError("HTTP Error")

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    with pytest.raises(requests.HTTPError):
        RightmoveAdapter.fetch("https://example.com")


@pytest.mark.skip(
    reason="Retry mechanism is handled by requests' adapter and is not directly testable with this mock setup."
)
def test_fetch_retry_mechanism(monkeypatch):
    # Not directly testable with monkeypatch
    pass


def test_fetch_json_ld_missing_fields(monkeypatch):
    html = '<html><script type=\'application/ld+json\'>{"@type": "Offer", "itemOffered": {"address": {}}, "price": null}</script></html>'

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["address"] is None
    assert result["price"] is None


def test_fetch_multiple_json_ld_scripts(monkeypatch):
    html = (
        "<html>"
        "<script type='application/ld+json'>not json</script>"
        '<script type=\'application/ld+json\'>{"@type": "Offer", "itemOffered": {"address": {"streetAddress": "Valid Address"}}, "price": 123}</script>'
        "</html>"
    )

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["address"] == "Valid Address"
    assert result["price"] == "£123"


def test_fetch_next_data_missing_fields(monkeypatch):
    html = '<html><script id=\'__NEXT_DATA__\' type=\'application/json\'>{"props": {"pageProps": {"initialReduxState": {"propertySummary": {"listing": {}}}}}}</script></html>'

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["address"] is None
    assert result["price"] is None


def test_fetch_html_beds_bathrooms(monkeypatch):
    html = "<html><h1>Some Address</h1><dl><dt>Bedrooms</dt><dd>2</dd><dt>Bathrooms</dt><dd>1</dd></dl></html>"

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["beds"] == "2"
    assert result["bathrooms"] == "1"


def test_fetch_html_service_charge_variants(monkeypatch):
    html = "<html><p>Service Charge: £123</p><p>Service charge £456</p></html>"

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert result["service_charge"] in ["£123", "£456"]


def test_fetch_real_rightmove_html(monkeypatch):
    with open(
        r"apps/core/tests/test_samples/sample_rightmove_listing.html",
        encoding="utf-8",
    ) as f:
        html = f.read()

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch(
        "https://www.rightmove.co.uk/properties/159360596#/?channel=RES_BUY"
    )
    assert isinstance(result, dict)
    assert "url" in result
    assert "address" in result
    assert "price" in result
    assert "beds" in result
    assert "bathrooms" in result
    assert "summary" in result
    assert "service_charge" in result


def test_fetch_410_gone_returns_user_friendly_error(monkeypatch):
    class MockResponse:
        status_code = 410
        text = "Gone"

        def raise_for_status(self):
            http_error = requests.HTTPError("410 Gone")
            http_error.response = self
            raise http_error

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    result = RightmoveAdapter.fetch("https://example.com")
    assert "error" in result
    assert "listing is gone" in result["error"]


def test_fetch_next_data_invalid_json(monkeypatch):
    html = "<html><script id='__NEXT_DATA__' type='application/json'>Invalid JSON</script></html>"

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    with pytest.raises(ValueError):
        RightmoveAdapter.fetch("https://example.com")


def test_fetch_html_dt_without_dd(monkeypatch):
    html = "<html><dl><dt>Bedrooms</dt></dl></html>"

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    with pytest.raises(ValueError):
        RightmoveAdapter.fetch("https://example.com")


def test_fetch_html_no_fields(monkeypatch):
    html = "<html><body>No useful data here</body></html>"

    class MockResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        RightmoveAdapter.session, "get", lambda url, **kwargs: MockResponse()
    )
    with pytest.raises(ValueError):
        RightmoveAdapter.fetch("https://example.com")


# --- API/View integration tests ---
pytestmark = pytest.mark.django_db
from django.test import Client


@pytest.fixture
def client():
    return Client()


def test_rightmove_api_success(monkeypatch, client):
    def mock_fetch(url):
        return {
            "address": "123 Example St",
            "price": "£1000000",
            "summary": "A nice place",
        }

    monkeypatch.setattr(RightmoveAdapter, "fetch", mock_fetch)
    url = "/api/scrape/"
    response = client.post(url, {"url": "https://example.com"})
    assert response.status_code in (200, 201)
    assert "address" in response.json()
    assert response.json()["address"] == "123 Example St"


def test_rightmove_api_error(monkeypatch, client):
    def mock_fetch(url):
        raise ValueError("Could not parse property data")

    monkeypatch.setattr(RightmoveAdapter, "fetch", mock_fetch)
    url = "/api/scrape/"
    response = client.post(url, {"url": "https://example.com"})
    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.django_db
def test_scrape_api_smoke_e2e(client):
    """
    End-to-end smoke test: POST to /api/scrape/ with a real-looking Rightmove URL.
    Mocks the external Rightmove HTTP call and checks the full Django stack.
    """
    rightmove_url = "https://www.rightmove.co.uk/properties/12345678"
    # Minimal HTML with JSON-LD for the adapter to parse
    html = (
        "<html><script type='application/ld+json'>"
        '{"@type": "Offer", "itemOffered": {"address": {"streetAddress": "E2E Test Address"}}, "price": 123456}'
        "</script></html>"
    )
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            rightmove_url,
            body=html,
            status=200,
            content_type="text/html",
        )
        response = client.post("/api/scrape/", {"url": rightmove_url})
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "E2E Test Address"
        assert data["price"] == "£123456"
