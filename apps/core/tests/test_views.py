# pylint: disable=missing-function-docstring, missing-class-docstring, missing-module-docstring
import pytest
from apps.core.adapters.rightmove import RightmoveAdapterError


@pytest.mark.django_db
def test_scrape_without_url(client):
    # Example: test a view that requires a URL param but none is given
    response = client.post("/api/scrape/", data={})
    assert response.status_code == 400
    assert "url" in response.json().get("error", "")


@pytest.fixture
def adapter_monkeypatch(monkeypatch):
    # Patch the fetch method on the RightmoveAdapter as a staticmethod
    def fake_fetch(url):
        return {"address": "stubbed", "price": "£123"}

    monkeypatch.setattr(
        "apps.core.adapters.rightmove.RightmoveAdapter.fetch", staticmethod(fake_fetch)
    )


@pytest.mark.django_db
def test_scrape_with_stub(adapter_monkeypatch, client):
    response = client.post("/api/scrape/", data={"url": "https://example.com"})
    if response.status_code != 200:
        print("DEBUG: Response status:", response.status_code)
        print("DEBUG: Response content:", response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "stubbed"
    assert data["price"] == "£123"


@pytest.mark.django_db
def test_scrape_adapter_valueerror(monkeypatch, client):
    # Simulate RightmoveAdapter.fetch raising ValueError
    def fake_fetch(url):
        raise ValueError("Could not parse property data")

    monkeypatch.setattr(
        "apps.core.adapters.rightmove.RightmoveAdapter.fetch", staticmethod(fake_fetch)
    )
    response = client.post("/api/scrape/", data={"url": "https://example.com"})
    assert response.status_code == 400
    assert "Could not parse property data" in response.json().get("error", "")


@pytest.mark.django_db
def test_scrape_adapter_exception(monkeypatch, client):
    # Simulate RightmoveAdapter.fetch raising a custom RightmoveAdapterError
    def fake_fetch(url):
        raise RightmoveAdapterError("Something went wrong!")

    monkeypatch.setattr(
        "apps.core.adapters.rightmove.RightmoveAdapter.fetch", staticmethod(fake_fetch)
    )
    response = client.post("/api/scrape/", data={"url": "https://example.com"})
    assert response.status_code == 500
    assert "unexpected error" in response.json().get("error", "").lower()


@pytest.mark.django_db
def test_scrape_append_row_called(monkeypatch, client, capsys):
    # Patch both fetch and append_row
    def fake_fetch(url):
        return {
            "url": url,
            "address": "stubbed",
            "price": "£123",
            "service_charge": "£300",
        }

    monkeypatch.setattr(
        "apps.core.adapters.rightmove.RightmoveAdapter.fetch", staticmethod(fake_fetch)
    )
    # Use capsys to capture print output and verify the call
    monkeypatch.setattr(
        "apps.sheets.sheets.append_row",
        lambda row: print(f"[sheets] append_row called with: {row}"),
    )
    response = client.post("/api/scrape/", data={"url": "https://example.com"})
    assert response.status_code == 200
    captured = capsys.readouterr()
    assert (
        "[sheets] append_row called with: ['https://example.com', 'stubbed', '£123', '£300']"
        in captured.out
    )
