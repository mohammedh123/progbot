from urllib.request import HTTPBasicAuthHandler

from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class FFLogsClient:
    API_URL = "https://www.fflogs.com/api/v2"
    OAUTH_TOKEN_URL = "https://www.fflogs.com/oauth/token"

    def __init__(self, client_id, client_secret) -> None:
        self.auth = HTTPBasicAuthHandler(client_id, client_secret)
        oauth_client = BackendApplicationClient(client_id=client_id)
        self.oauth_session = OAuth2Session(client=oauth_client)

        self._transport = RequestsHTTPTransport(url=self.API_URL + "/client")
        self._gql_client = Client(
            transport=self._transport, fetch_schema_from_transport=True
        )
