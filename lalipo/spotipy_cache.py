from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyAuthBase, SpotifyOauthError
from allauth.socialaccount.models import SocialToken, SocialApp
from datetime import datetime
import logging
import base64

import logging
import time
import warnings

import requests
# Workaround to support both python 2 & 3
import six
import six.moves.urllib.parse as urllibparse
from six.moves.urllib_parse import parse_qsl, urlparse


logger = logging.getLogger(__name__)

class SparisonCacheHandler(CacheHandler):

    def __init__(self, user):
        self.spotify_object = SocialToken.objects.get(account__provider="spotify", account__user=user)
        self.spotify_app = SocialApp.objects.first()

    def get_cached_token(self):
        # retrieve the token info from the `SocialToken` object
        self.spotify_object.refresh_from_db()
        token_info = {}

        token_info["access_token"] = self.spotify_object.token
        token_info["refresh_token"] = self.spotify_object.token_secret
        token_info["expires_at"] = int(self.spotify_object.expires_at.timestamp())
        token_info["scope"] = " ".join(self.spotify_app.settings["SCOPE"])

        return token_info

    def save_token_to_cache(self, token_info):
        # save the token info back to the `SocialToken` object
        # notice that we're saving the token info back to the same place that we retrieved it from
        # in `get_cached_token`; this is crucial

        self.spotify_object.token = token_info["access_token"]
        self.spotify_object.token_secret = token_info["refresh_token"]
        self.spotify_object.expires_at = datetime.fromtimestamp(token_info["expires_at"])
        self.spotify_object.scope = token_info["scope"]


def _make_authorization_headers(client_id, client_secret):
    auth_header = base64.b64encode(
        six.text_type(client_id + ":" + client_secret).encode("ascii")
    )
    return {"Authorization": "Basic %s" % auth_header.decode("ascii")}

class CustomAuth(SpotifyAuthBase):
    """
    Implements Authorization Code Flow for Spotify's OAuth implementation.
    """
    OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
    OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(
            self,
            client_id,
            client_secret,
            cache_handler,
            redirect_uri=None,
            state=None,
            scope=None,
            proxies=None,
            show_dialog=False,
            requests_session=True,
            requests_timeout=None,
    ):
        """
        Creates a SpotifyOAuth object

        Parameters:
             * client_id: Must be supplied or set as environment variable
             * client_secret: Must be supplied or set as environment variable
             * redirect_uri: Must be supplied or set as environment variable
             * state: Optional, no verification is performed
             * scope: Optional, either a list of scopes or comma separated string of scopes.
                      e.g, "playlist-read-private,playlist-read-collaborative"
             * proxies: Optional, proxy for the requests library to route through
             * show_dialog: Optional, interpreted as boolean
             * requests_session: A Requests session
             * requests_timeout: Optional, tell Requests to stop waiting for a response after
                                 a given number of seconds
             * open_browser:
                             authorize a user
             * cache_handler: An instance of the `CacheHandler` class to handle
                              getting and saving cached authorization tokens.
                              Optional, will otherwise use `CacheFileHandler`.
                              (takes precedence over `cache_path` and `username`)
        """

        super().__init__(requests_session)

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state
        self.scope = self._normalize_scope(scope)
        self.cache_handler = cache_handler
        self.proxies = proxies
        self.requests_timeout = requests_timeout
        self.show_dialog = show_dialog

    def get_authorize_url(self, state=None):
        """ Gets the URL to use to authorize this app
        """
        payload = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
        }
        if self.scope:
            payload["scope"] = self.scope
        if state is None:
            state = self.state
        if state is not None:
            payload["state"] = state
        if self.show_dialog:
            payload["show_dialog"] = True

        urlparams = urllibparse.urlencode(payload)

        return "%s?%s" % (self.OAUTH_AUTHORIZE_URL, urlparams)

    def parse_response_code(self, url):
        """ Parse the response code in the given response url

            Parameters:
                - url - the response url
        """
        _, code = self.parse_auth_response_url(url)
        if code is None:
            return url
        else:
            return code

    def validate_token(self, token_info):
        if token_info is None:
            return None

        # if scopes don't match, then bail
        if "scope" not in token_info or not self._is_scope_subset(
                self.scope, token_info["scope"]
        ):
            raise Exception("Unexpected token scope")

        if self.is_token_expired(token_info):
            token_info = self.refresh_access_token(
                token_info["refresh_token"]
            )
            return token_info

        return token_info

    @staticmethod
    def parse_auth_response_url(url):
        query_s = urlparse(url).query
        form = dict(parse_qsl(query_s))
        if "error" in form:
            raise SpotifyOauthError("Received error from auth server: "
                                    "{}".format(form["error"]),
                                    error=form["error"])
        return tuple(form.get(param) for param in ["state", "code"])

    def _make_authorization_headers(self):
        return _make_authorization_headers(self.client_id, self.client_secret)

    def get_access_token(self, code=None, as_dict=True):
        """ Gets the access token for the app given the code

            Parameters:
                - code - the response code
                - as_dict - a boolean indicating if returning the access token
                            as a token_info dictionary, otherwise it will be returned
                            as a string.
        """
        if as_dict:
            warnings.warn(
                "You're using 'as_dict = True'."
                "get_access_token will return the token string directly in future "
                "versions. Please adjust your code accordingly, or use "
                "get_cached_token instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        token_info = self.validate_token(self.cache_handler.get_cached_token())
        if token_info is not None:
            if self.is_token_expired(token_info):
                token_info = self.refresh_access_token(
                    token_info["refresh_token"]
                )
            return token_info if as_dict else token_info["access_token"]


    def refresh_access_token(self, refresh_token):
        payload = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        headers = self._make_authorization_headers()

        logger.debug(
            "sending POST request to %s with Headers: %s and Body: %r",
            self.OAUTH_TOKEN_URL, headers, payload
        )

        try:
            response = self._session.post(
                self.OAUTH_TOKEN_URL,
                data=payload,
                headers=headers,
                proxies=self.proxies,
                timeout=self.requests_timeout,
            )
            response.raise_for_status()
            token_info = response.json()
            token_info = self._add_custom_values_to_token_info(token_info)
            if "refresh_token" not in token_info:
                token_info["refresh_token"] = refresh_token
            self.cache_handler.save_token_to_cache(token_info)
            return token_info
        except requests.exceptions.HTTPError as http_error:
            self._handle_oauth_error(http_error)

    def _add_custom_values_to_token_info(self, token_info):
        """
        Store some values that aren't directly provided by a Web API
        response.
        """
        token_info["expires_at"] = int(time.time()) + token_info["expires_in"]
        token_info["scope"] = self.scope
        return token_info
