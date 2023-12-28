from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyOAuth
from allauth.socialaccount.models import SocialToken, SocialApp
from datetime import datetime
import logging

import logging
import warnings

from django.conf import settings

logger = logging.getLogger(__name__)

class SocialAppCacheHandler(CacheHandler):

    def __init__(self, user):
        self.spotify_object = SocialToken.objects.get(account__provider="spotify", account__user=user)
        spotify_app = SocialApp.objects.first()
        if spotify_app:
            self.scope = " ".join(spotify_app.settings["SCOPE"])
        else:
            self.scope = " ".join(settings.SOCIALACCOUNT_PROVIDERS["spotify"]["SCOPE"])

    def get_cached_token(self):
        # retrieve the token info from the `SocialToken` object
        self.spotify_object.refresh_from_db()
        token_info = {}

        token_info["access_token"] = self.spotify_object.token
        token_info["refresh_token"] = self.spotify_object.token_secret
        token_info["expires_at"] = int(self.spotify_object.expires_at.timestamp())
        # token_info["scope"] = self.scope

        return token_info

    def save_token_to_cache(self, token_info):
        # save the token info back to the `SocialToken` object
        # notice that we're saving the token info back to the same place that we retrieved it from
        # in `get_cached_token`; this is crucial

        self.spotify_object.token = token_info["access_token"]
        self.spotify_object.token_secret = token_info["refresh_token"]
        self.spotify_object.expires_at = datetime.fromtimestamp(token_info["expires_at"])
        # self.spotify_object.scope = token_info["scope"]


class CustomAuth(SpotifyOAuth):
    """
    Always use the cache to store/retrieve the token.
    """

    def validate_token(self, token_info):
        """Raise in case of problematic scope instead of returning None - better for debugging"""
        if token_info is None:
            return None

        # # if scopes don't match, then bail
        # if "scope" not in token_info or not self._is_scope_subset(
        #         self.scope, token_info["scope"]
        # ):
        #     raise Exception(f"Unexpected token scope:\n{self.scope}\n{token_info.get('scope', None)}")

        if self.is_token_expired(token_info):
            token_info = self.refresh_access_token(
                token_info["refresh_token"]
            )

        return token_info

    def get_access_token(self, code=None, as_dict=True):
        """About same as from parent class, except always use token from cache"""
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

