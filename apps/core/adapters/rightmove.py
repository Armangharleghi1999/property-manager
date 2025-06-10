# pylint: disable=missing-function-docstring, missing-class-docstring, missing-module-docstring
import re
import json
import logging
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RightmoveAdapterError(Exception):
    """Custom exception for unexpected RightmoveAdapter errors."""

    pass


class RightmoveAdapter:
    # --- shared session with retries & headers ------------------------------
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }
    )

    @staticmethod
    def fetch(url: str) -> Dict[str, Optional[str]]:
        clean_url = url.split("#")[0]
        logging.debug("Fetching URL: %r", clean_url)

        try:
            resp = RightmoveAdapter.session.get(clean_url, timeout=10)
            resp.raise_for_status()
        except requests.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 410
            ):
                logging.error("Listing gone (410): %r", clean_url)
                return {
                    "error": "It seems the listing is gone or the property is sold."
                }
            logging.error("HTTP error fetching %r: %s", clean_url, e)
            raise
        except requests.exceptions.RequestException as e:
            logging.error("Request exception for %r: %s", clean_url, e)
            raise

        body = resp.text
        logging.debug("HTTP %d received, body length=%d", resp.status_code, len(body))

        soup = BeautifulSoup(body, "html.parser")

        # --- 1) JSON-LD parsing ---------------------------------------------
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if data.get("@type") == "Offer":
                    address = (
                        data.get("itemOffered", {})
                        .get("address", {})
                        .get("streetAddress")
                    )
                    price = data.get("price")
                    logging.debug("Parsed JSON-LD Offer object")
                    return {
                        "url": clean_url,
                        "address": address,
                        "price": f"£{price}" if price else None,
                        "beds": None,
                        "bathrooms": None,
                        "summary": None,
                        "service_charge": None,
                    }
            except (ValueError, TypeError):
                continue
        logging.debug("Found 0 usable JSON-LD scripts")

        # --- 2) Next.js __NEXT_DATA__ fallback --------------------------------
        next_data = soup.find("script", id="__NEXT_DATA__", type="application/json")
        if next_data:
            try:
                payload = json.loads(next_data.string or "{}")
                props = payload.get("props", {})
                pageProps = props.get("pageProps", {})
                listing = (
                    pageProps.get("initialReduxState", {})
                    .get("propertySummary", {})
                    .get("listing", {})
                )
                # Robustly check for propertyDescription in all likely locations
                desc = None
                if "propertyDescription" in pageProps:
                    desc = pageProps["propertyDescription"].get("description")
                elif "propertyDescription" in props:
                    desc = props["propertyDescription"].get("description")
                elif "propertyDescription" in payload.get("props", {}):
                    desc = payload["props"]["propertyDescription"].get("description")
                elif "propertyDescription" in pageProps.get("initialReduxState", {}):
                    desc = pageProps["initialReduxState"]["propertyDescription"].get(
                        "description"
                    )
                print("DEBUG: desc:", desc)
                logging.debug("Parsed __NEXT_DATA__ model")
                return {
                    "url": clean_url,
                    "address": listing.get("displayAddress"),
                    "price": listing.get("formattedPrice"),
                    "beds": listing.get("bedroomNumber"),
                    "bathrooms": listing.get("bathroomNumber"),
                    "summary": desc,
                    "service_charge": listing.get("serviceCharge"),
                }
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("Failed to parse __NEXT_DATA__: %s", e)

        # --- 3) HTML fallback via BeautifulSoup -----------------------------
        logging.debug("Attempting HTML fallback parsing")
        address = None
        price = None
        beds = None
        bathrooms = None
        summary = None
        service_charge = None

        # address from <h1>
        if h1 := soup.find("h1"):
            address = h1.get_text(strip=True)

        # price: first “£123,456”
        if m := re.search(r"£[\d,]+", body):
            price = m.group()

        # service charge: “Service Charge … £X”
        if sc := re.search(r"Service\s*Charge.*?(£[\d,]+)", body, flags=re.IGNORECASE):
            service_charge = sc.group(1)

        # summary: page’s meta[name="description"]
        if meta := soup.find("meta", attrs={"name": "description"}):
            summary = meta.get("content", "").strip() or None

        # beds & bathrooms: look up <dt> label + next <dd>
        for dt in soup.select("dl dt"):
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            val = dd.get_text(strip=True)
            if "bedroom" in label:
                beds = val
            elif "bathroom" in label:
                bathrooms = val

        # if any of the key fields got populated, return the fallback
        if any([address, price, beds, bathrooms, service_charge, summary]):
            logging.info(
                "HTML fallback parsed: address=%r, price=%r, beds=%r, "
                "bathrooms=%r, summary=%r, service_charge=%r",
                address,
                price,
                beds,
                bathrooms,
                summary,
                service_charge,
            )
            return {
                "url": clean_url,
                "address": address,
                "price": price,
                "beds": beds,
                "bathrooms": bathrooms,
                "summary": summary,
                "service_charge": service_charge,
            }

        # --- all strategies failed ------------------------------------------
        # If the response was not 2xx, raise HTTPError (for test_fetch_non_200_status_code)
        if resp.status_code != 200:
            resp.raise_for_status()
        logging.error("All parsing strategies failed for %r", clean_url)
        raise ValueError("PAGE_MODEL JSON extraction failed")
