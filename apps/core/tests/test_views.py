import pytest


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
