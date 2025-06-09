import requests
from bs4 import BeautifulSoup


class RightmoveAdapter:
    @staticmethod
    def fetch(url: str) -> dict:
        # TODO: implement real parsing logic with BeautifulSoup
        return {
            "url": url,
            "address": "123 Example Street, London",
            "price": "£1,000,000",
            "service_charge": "£200",
        }
