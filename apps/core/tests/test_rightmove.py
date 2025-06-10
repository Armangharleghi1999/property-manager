import logging

logging.disable(logging.CRITICAL)

import unittest
from unittest.mock import patch
from apps.core.adapters.rightmove import RightmoveAdapter
import requests


class TestRightmoveAdapter(unittest.TestCase):

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_successful_json_ld_parsing(self, mock_get):
        """Test successful parsing of JSON-LD data."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><script type='application/ld+json'>"
            '{"@type": "Offer", "itemOffered": {"address": {"streetAddress": "123 Example St"}}, "price": 1000000}'
            "</script></html>"
        )

        result = RightmoveAdapter.fetch("https://example.com")
        self.assertEqual(result["address"], "123 Example St")
        self.assertEqual(result["price"], "£1000000")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_get.side_effect = requests.HTTPError("HTTP Error")

        with self.assertRaises(requests.HTTPError):
            RightmoveAdapter.fetch("https://example.com")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_next_data_parsing(self, mock_get):
        """Test parsing of Next.js __NEXT_DATA__ fallback."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><script id='__NEXT_DATA__' type='application/json'>"
            '{"props": {"pageProps": {"initialReduxState": {"propertySummary": {"listing": {"displayAddress": "123 Example St", "formattedPrice": "£1,000,000"}}, "propertyDescription": {"description": "A beautiful property"}}}}}'
            "</script></html>"
        )

        result = RightmoveAdapter.fetch("https://example.com")
        print("DEBUG: result from __NEXT_DATA__ test:", result)
        self.assertEqual(result["address"], "123 Example St")
        self.assertEqual(result["price"], "£1,000,000")
        self.assertEqual(result["summary"], "A beautiful property")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_html_fallback(self, mock_get):
        """Test HTML fallback parsing with real Rightmove HTML sample."""
        with open(
            r"apps/core/tests/test_samples/sample_rightmove_listing.html",
            encoding="utf-8",
        ) as f:
            html = f.read()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = html
        result = RightmoveAdapter.fetch("https://example.com")
        self.assertIn("address", result)
        self.assertIn("price", result)
        self.assertIn("service_charge", result)

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_all_strategies_fail(self, mock_get):
        """Test that fetch raises ValueError when all parsing strategies fail."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html></html>"

        with self.assertRaises(ValueError):
            RightmoveAdapter.fetch("https://example.com")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_service_charge_parsing(self, mock_get):
        """Test parsing of service charge from HTML."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><p>Service charge: £300</p></html>"

        result = RightmoveAdapter.fetch("https://example.com")
        self.assertEqual(result["service_charge"], "£300")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout

        with self.assertRaises(requests.exceptions.Timeout):
            RightmoveAdapter.fetch("https://example.com")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_invalid_json_ld(self, mock_get):
        """Test handling of invalid JSON-LD data."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><script type='application/ld+json'>Invalid JSON</script></html>"
        )

        with self.assertRaises(ValueError):
            RightmoveAdapter.fetch("https://example.com")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_malformed_html(self, mock_get):
        """Test handling of malformed HTML."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><h1>123 Example St"

        result = RightmoveAdapter.fetch("https://example.com")
        self.assertEqual(result["address"], "123 Example St")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_non_200_status_code(self, mock_get):
        """Test handling of non-200 HTTP status codes."""
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        with self.assertRaises(requests.HTTPError):
            RightmoveAdapter.fetch("https://example.com")

    @unittest.skip(
        "Retry mechanism is handled by requests' adapter and is not directly testable with this mock setup."
    )
    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_retry_mechanism(self, mock_get):
        """Test retry mechanism for transient errors."""
        mock_get.side_effect = [
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectionError,
            unittest.mock.Mock(status_code=200, text="<html></html>"),
        ]

        with self.assertRaises(ValueError):
            RightmoveAdapter.fetch("https://example.com")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_json_ld_missing_fields(self, mock_get):
        """Test JSON-LD with missing address and price fields."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><script type='application/ld+json'>"
            '{"@type": "Offer", "itemOffered": {"address": {}}, "price": null}'
            "</script></html>"
        )
        result = RightmoveAdapter.fetch("https://example.com")
        self.assertIsNone(result["address"])
        self.assertIsNone(result["price"])

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_multiple_json_ld_scripts(self, mock_get):
        """Test multiple JSON-LD scripts, only one valid."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html>"
            "<script type='application/ld+json'>not json</script>"
            "<script type='application/ld+json'>"
            '{"@type": "Offer", "itemOffered": {"address": {"streetAddress": "Valid Address"}}, "price": 123}'
            "</script>"
            "</html>"
        )
        result = RightmoveAdapter.fetch("https://example.com")
        self.assertEqual(result["address"], "Valid Address")
        self.assertEqual(result["price"], "£123")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_next_data_missing_fields(self, mock_get):
        """Test __NEXT_DATA__ with missing fields."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><script id='__NEXT_DATA__' type='application/json'>"
            '{"props": {"pageProps": {"initialReduxState": {"propertySummary": {"listing": {}}}}}}'
            "</script></html>"
        )
        result = RightmoveAdapter.fetch("https://example.com")
        self.assertIsNone(result["address"])
        self.assertIsNone(result["price"])

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_html_beds_bathrooms(self, mock_get):
        """Test HTML fallback for beds and bathrooms extraction."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><h1>Some Address</h1>"
            "<dl><dt>Bedrooms</dt><dd>2</dd><dt>Bathrooms</dt><dd>1</dd></dl>"
            "</html>"
        )
        result = RightmoveAdapter.fetch("https://example.com")
        self.assertEqual(result["beds"], "2")
        self.assertEqual(result["bathrooms"], "1")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_html_service_charge_variants(self, mock_get):
        """Test HTML fallback for service charge regex edge cases."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><p>Service Charge: £123</p><p>Service charge £456</p></html>"
        )
        result = RightmoveAdapter.fetch("https://example.com")
        self.assertIn(result["service_charge"], ["£123", "£456"])

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_real_rightmove_html(self, mock_get):
        """Test fetch with a real Rightmove HTML sample."""
        with open(
            r"apps/core/tests/test_samples/sample_rightmove_listing.html",
            encoding="utf-8",
        ) as f:
            html = f.read()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = html
        result = RightmoveAdapter.fetch(
            "https://www.rightmove.co.uk/properties/159360596#/?channel=RES_BUY"
        )
        # The real sample is mostly empty, but we can check the structure
        self.assertIsInstance(result, dict)
        self.assertIn("url", result)
        self.assertIn("address", result)
        self.assertIn("price", result)
        self.assertIn("beds", result)
        self.assertIn("bathrooms", result)
        self.assertIn("summary", result)
        self.assertIn("service_charge", result)

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_410_gone_returns_user_friendly_error(self, mock_get):
        """Test handling of HTTP 410 Gone with user-friendly error message."""
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 410
        mock_response.text = "Gone"
        http_error = requests.HTTPError("410 Gone")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = RightmoveAdapter.fetch("https://example.com")
        self.assertIn("error", result)
        self.assertIn("listing is gone", result["error"])

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_next_data_invalid_json(self, mock_get):
        """Test __NEXT_DATA__ with invalid JSON triggers except block."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><script id='__NEXT_DATA__' type='application/json'>Invalid JSON</script></html>"
        # Should fall through to HTML fallback and raise ValueError (no fields)
        with self.assertRaises(ValueError):
            RightmoveAdapter.fetch("https://example.com")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_html_dt_without_dd(self, mock_get):
        """Test HTML fallback with <dt> but no <dd> sibling."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><dl><dt>Bedrooms</dt></dl></html>"
        # Should raise ValueError because no fields are extractable
        with self.assertRaises(ValueError):
            RightmoveAdapter.fetch("https://example.com")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.session.get")
    def test_fetch_html_no_fields(self, mock_get):
        """Test HTML fallback with no extractable fields."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><body>No useful data here</body></html>"
        with self.assertRaises(ValueError):
            RightmoveAdapter.fetch("https://example.com")


# --- API/View integration tests ---
try:
    from django.test import Client
    from django.urls import reverse
    import pytest
except ImportError:
    Client = None
    reverse = None
    pytest = None


@unittest.skipUnless(Client and reverse, "Django test client not available")
class TestRightmoveViewIntegration(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.fetch")
    def test_rightmove_api_success(self, mock_fetch):
        """Test API returns property data from RightmoveAdapter."""
        mock_fetch.return_value = {
            "address": "123 Example St",
            "price": "£1000000",
            "summary": "A nice place",
        }
        url = "/api/scrape/"
        response = self.client.post(url, {"url": "https://example.com"})
        # Accept 200 or 201 for now, but 200 is preferred for scrape endpoints
        self.assertIn(
            response.status_code,
            (200, 201),
            f"Unexpected status: {response.status_code}, content: {response.content}",
        )
        self.assertIn("address", response.json())
        self.assertEqual(response.json()["address"], "123 Example St")

    @patch("apps.core.adapters.rightmove.RightmoveAdapter.fetch")
    def test_rightmove_api_error(self, mock_fetch):
        """Test API returns error message when adapter fails."""
        mock_fetch.side_effect = ValueError("Could not parse property data")
        url = "/api/scrape/"
        response = self.client.post(url, {"url": "https://example.com"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())


if __name__ == "__main__":
    unittest.main()
