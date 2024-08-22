import httpx
from pyzotero import zotero
import urllib.parse
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ZoteroBackend(zotero.Zotero):
    def __init__(self, library_id, library_type, api_key):
        super().__init__(library_id, library_type, api_key)
        self.client = httpx.Client(verify=False)

    def _retrieve_data(self, request=None, params=None):
        """
        Override _retrieve_data to use httpx instead of requests
        """
        full_url = zotero.build_url(self.endpoint, request)
        self.self_link = request
        self._check_backoff()

        headers = self.default_headers()
        
        logger.debug(f"Making request to URL: {full_url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Params: {params}")

        try:
            # Ensure the URL is properly encoded
            encoded_url = urllib.parse.quote(full_url, safe=':/?&=')
            self.request = self.client.get(
                url=encoded_url,
                headers=headers,
                params=params
            )
            self.request.encoding = "utf-8"
            self.request.raise_for_status()
        except httpx.RequestError as exc:
            logger.error(f"Request error: {exc}")
            raise zotero.ze.HTTPError(str(exc))
        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTP status error: {exc}")
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
        print(collections)
    except Exception as e:
        print(f"An error occurred: {str(e)}")