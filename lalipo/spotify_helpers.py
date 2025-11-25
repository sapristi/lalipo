import pydantic
import itertools

from django.conf import settings
from allauth.socialaccount.models import SocialApp
from spotipy import Spotify
from lalipo.spotipy_cache import SocialAppCacheHandler, CustomAuth

class SpotifyApp:
    def __init__(self):
        self.scope = ['playlist-modify-public', 'playlist-modify-private']

        # Not sure how useful that is
        spotify_app = SocialApp.objects.filter(provider="spotify").first()
        if spotify_app:
            self.client_id=spotify_app.settings.get('client_id')
            self.client_secret=spotify_app.settings.get('secret')
        else:
            self.client_id = settings.SOCIALACCOUNT_PROVIDERS["spotify"]["APPS"][0]["client_id"]
            self.client_secret = settings.SOCIALACCOUNT_PROVIDERS["spotify"]["APPS"][0]["secret"]

    def for_user(self, user):
        sp = Spotify(
            client_credentials_manager=CustomAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=settings.HOST,
                scope=self.scope,
                cache_handler=SocialAppCacheHandler(user=user),
            )
        )
        return sp

spotify_app = SpotifyApp()


class BaseModel(pydantic.BaseModel):
    class Config:
        extra = "ignore"


class Artist(BaseModel):
    href: str
    id: str
    name: str
    type: str
    uri: str

    def __repr__(self):
        return self.name

class ExternalUrls(BaseModel):
    spotify: str


class Track(BaseModel):
    artists: list[Artist]
    duration_ms: int
    id: str
    name: str
    track_number: int
    uri: str
    external_urls: ExternalUrls


class Album(BaseModel):
    artists: list[Artist]
    album_type: str
    id: str
    name: str
    release_date: str
    release_date_precision: str
    total_tracks: int
    uri: str


def get_tracks_from_plages_musicales(sp, lines: list[str]):
    print("Parsing plages musicales")
    for line in lines:
        artist, title = line.split("\t")
        if title.startswith("single :") or title.startswith("singles :"):
            title = title.split(":", maxsplit=1)[1].strip()
            tracks = title.split(" + ")
            for track in tracks:
                results = sp.search(q=f"artist:{artist} track:{track}", type="track")["tracks"]
                if len(results["items"]) == 0:
                    print(f"Failed to find track for {artist} - {track}")
                    pass
                else:
                    track = Track(**results["items"][0])
                    print("FOUND TRACK", track)
                    yield track

        else:
            results = sp.search(q=f"artist:{artist} album:{title}", type="album")["albums"]
            if len(results["items"]) == 0:
                print(f"Failed to find album for {artist} - {title}")
                continue
            album = Album(**results["items"][0])
            print("FOUND ALBUM", album)
            tracks = sp.album_tracks(album.uri)
            for track in tracks["items"]:
                yield Track(**track)


def get_tracks_from_stoned_circus(sp, lines: list[str]):
    print("Parsing stoned circus")
    for line in lines:
        artist = ""
        track = ""
        add_to_track = False
        for word in line.split():
            if add_to_track:
                track += " " + word
            else:
                if word != word.upper():
                    add_to_track = True
                    track += " " + word
                else:
                    artist += " " + word
        results = sp.search(q=f"artist:{artist} track:{track}", type="track")["tracks"]
        if len(results["items"]) == 0:
            pass
        else:
            track = Track(**results["items"][0])
            yield track

def get_tracks_auto(sp, lines: list[str]):
    for line in lines:
        if "\t" in line:
            artist, track = [part.strip() for part in line.split("\t", maxsplit=1) ]
            search_term = f"artist:{artist} track:{track}"
        else:
            search_term = line
        results = sp.search(q=search_term, type="track")["tracks"]
        if len(results["items"]) == 0:
            print(f"Failed to find track for '{search_term}'")
        else:
            track = Track(**results["items"][0])
            print("FOUND TRACK", track)
            yield track



def create_playlist(sp, title, track_uris):

    playlist = sp.user_playlist_create(
        user=sp.current_user()["id"],
        name=title
    )
    print("MADE playlist", playlist)

    track_uris_gen = (track_uri for track_uri in track_uris)
    while True:
        tracks_batch = list(itertools.islice(track_uris_gen, 100))
        if len(tracks_batch) == 0:
            break
        sp.playlist_add_items(
            playlist_id=playlist["id"],
            items=[track_uri for track_uri in tracks_batch]
        )

    return playlist
