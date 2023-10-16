import spotipy
from spotipy.oauth2 import SpotifyOAuth
from enum import Enum


# scope = "playlist-modify-public,playlist-modify-private"
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


def make_playlist(sp, title):
    playlist = sp.user_playlist_create(
        user=sp.current_user()["id"],
        name=title
    )
    return playlist


def get_tracks_from_plages_musicales(sp, input: str):
    for line in input.splitlines():
        artist, title = line.split("\t")
        if title.startswith("single  :"):
            title = title.split("single  :")[1].strip()
            tracks = title.split(" + ")
            for track in tracks:
                results = sp.search(q=f"artist:{artist} track:{track}", type="track")["tracks"]
                if len(results["items"]) == 0:
                    pass
                else:
                    yield results["items"][0]
        else:
            results = sp.search(q=f"artist:{artist} album:{title}", type="album")["albums"]
            if len(results["items"]) == 0:
                pass
            tracks = sp.album_tracks(results["items"][0]["uri"])
            for track in tracks["items"]:
                yield track


def get_tracks_from_stoned_circus(sp, input: str):
    for line in input.splitlines():
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
                yield results["items"][0]

class Source(Enum):
    stoned_circus = (get_tracks_from_stoned_circus,)
    plages_musicales = (get_tracks_from_plages_musicales,)

    def __init__(self, val):
        self.val = val

    @property
    def value(self):
        return self.name

def main(source: Source, value: str):
    for val in source.val(value):
        print(val)
