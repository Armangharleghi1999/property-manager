import pytest
from django.urls import reverse
from rest_framework.test import APIClient

def api_client():
    return APIClient()

def test_scrape_without_url(api_client):
    url = reverse('scrape')
    response = api_client.post(url, {}, format='json')
    assert response.status_code == 400

def test_scrape_with_stub(adapter_monkeypatch, api_client, monkeypatch):
    # monkeypatch the adapter and sheets to avoid external calls
    from apps.core.adapters.rightmove import RightmoveAdapter
    from apps.sheets.sheets import append_row

    monkeypatch.setattr(RightmoveAdapter, 'fetch', lambda url: {
        'url': url, 'address': 'Addr', 'price': '100', 'service_charge': '10'
    })
    monkeypatch.setattr('apps.sheets.sheets.append_row', lambda values: None)

    url = reverse('scrape')
    response = api_client.post(url, {'url': 'https://test'}, format='json')
    assert response.status_code == 201
    assert response.data['url'] == 'https://test'