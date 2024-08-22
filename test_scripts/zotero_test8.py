import httpx
from pyzotero import zotero
import urllib.parse
import logging
from types import SimpleNamespace
import re
import requests
import ssl

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RequestsLikeResponse:
    def __init__(self, httpx_response):
        self.httpx_response = httpx_response
        self.status_code = httpx_response.status_code
        self.headers = httpx_response.headers
        self.encoding = httpx_response.encoding
        self.url = str(httpx_response.url)
        self.text = httpx_response.text
        self.content = httpx_response.content
        self.request = SimpleNamespace(method=httpx_response.request.method)
        self.links = self._parse_links(httpx_response.headers.get('Link', ''))

    def json(self):
        return self.httpx_response.json()

    def raise_for_status(self):
        self.httpx_response.raise_for_status()

    def _parse_links(self, link_header):
        links = {}
        if link_header:
            link_pattern = re.compile(r'<([^>]+)>;\s*rel="([^"]+)"')
            matches = link_pattern.findall(link_header)
            for url, rel in matches:
                links[rel] = {'url': url}
        return links

class ZoteroBackend(zotero.Zotero):
    def __init__(self, library_id, library_type, api_key):
        super().__init__(library_id, library_type, api_key)
        self.httpx_client = httpx.Client(verify=False)

    def _retrieve_data(self, request=None, params=None):
        """
        First attempt a normal HTTPS connection, then fall back to httpx with SSL verification disabled if needed
        """
        full_url = zotero.build_url(self.endpoint, request)
        self.self_link = request
        self._check_backoff()

        headers = self.default_headers()

        try:
            # First, try the normal pyzotero approach
            self.request = requests.get(
                url=full_url,
                headers=headers,
                params=params
            )
            self.request.raise_for_status()
        except requests.exceptions.SSLError:
            logger.warning("SSL error occurred. Falling back to httpx with SSL verification disabled.")
            try:
                # Fall back to httpx with SSL verification disabled
                encoded_url = urllib.parse.quote(full_url, safe=':/?&=')
                httpx_response = self.httpx_client.get(
                    url=encoded_url,
                    headers=headers,
                    params=params
                )
                self.request = RequestsLikeResponse(httpx_response)
                self.request.raise_for_status()
            except httpx.RequestError as exc:
                logger.error(f"Request error: {exc}")
                raise zotero.ze.HTTPError(str(exc))
            except httpx.HTTPStatusError as exc:
                logger.error(f"HTTP status error: {exc}")
                error_handler(self, self.request, exc)
        except requests.exceptions.RequestException as exc:
            logger.error(f"Request error: {exc}")
            error_handler(self, self.request, exc)

        backoff = self.request.headers.get("backoff") or self.request.headers.get("retry-after")
        if backoff:
            self._set_backoff(backoff)

        return self.request

def error_handler(zot, response, exc):
    error_codes = {
        400: zotero.ze.UnsupportedParams,
        401: zotero.ze.UserNotAuthorised,
        403: zotero.ze.UserNotAuthorised,
        404: zotero.ze.ResourceNotFound,
        409: zotero.ze.Conflict,
        412: zotero.ze.PreConditionFailed,
        413: zotero.ze.RequestEntityTooLarge,
        428: zotero.ze.PreConditionRequired,
        429: zotero.ze.TooManyRequests,
    }

    def err_msg(response):
        return "\nCode: %s\nURL: %s\nMethod: %s\nResponse: %s" % (
            response.status_code,
            response.url,
            response.request.method,
            response.text,
        )

    logger.error(f"Error response: {err_msg(response)}")

    if error_codes.get(response.status_code):
        if response.status_code == 429:
            delay = response.headers.get("backoff") or response.headers.get("retry-after")
            if not delay:
                raise zotero.ze.TooManyRetries(
                    "You are being rate-limited and no backoff or retry duration has been received from the server. Try again later"
                )
            else:
                zot._set_backoff(delay)
        else:
            raise error_codes.get(response.status_code)(err_msg(response))
    else:
        raise zotero.ze.HTTPError(err_msg(response))

from decouple import config

# Usage
if __name__ == "__main__":
    library_id = config("ZOTERO_USER_ID")
    library_type = "user"
    api_key = config("ZOTERO_API_KEY")

    zotero_backend = ZoteroBackend(library_id, library_type, api_key)
    
    try:
        collections = zotero_backend.collections()
        #print(collections)
        logger.info(f"Retrieved {len(collections)} collections")
        for collection in collections:
            logger.debug(f"Collection: {collection.get('data', {}).get('name', 'Unknown')}")
    except Exception as e:
        logger.exception("An error occurred")
        print(f"An error occurred: {str(e)}")