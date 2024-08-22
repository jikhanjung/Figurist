import httpx
from pyzotero import zotero

class ZoteroBackend(zotero.Zotero):
    def __init__(self, library_id, library_type, api_key):
        super().__init__(library_id, library_type, api_key)
        self.client = httpx.Client(verify=False)

    def _request(self, method, url, **kwargs):
        """Override the _request method to use httpx instead of requests"""
        headers = kwargs.pop('headers', {})
        headers.update(self.default_headers())
        
        try:
            response = self.client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
        except httpx.RequestError as e:
            raise zotero.ze.HTTPError(str(e))
        except httpx.HTTPStatusError as e:
            error_handler(self, response, e)

        return response

# Modify the error_handler function to work with httpx responses
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