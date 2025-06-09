import pytest
from apps.core.adapters.rightmove import RightmoveAdapter

@ pytest.mark.parametrize("url", [
    "https://www.rightmove.co.uk/property-for-sale/example-1",
    "https://www.rightmove.co.uk/property-for-sale/example-2",
])
def test_fetch_returns_expected_keys(url):
    data = RightmoveAdapter.fetch(url)
    assert set(data.keys()) == {"url", "address", "price", "service_charge"}
    assert data['url'] == url