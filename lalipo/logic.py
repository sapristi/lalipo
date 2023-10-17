from enum import Enum
import pydantic



def make_playlist(sp, title):
    playlist = sp.user_playlist_create(
        user=sp.current_user()["id"],
        name=title
    )
    return playlist

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

class Track(BaseModel):
    artists: list[Artist]
    duration_ms: int
    id: str
    name: str
    track_number: int
    uri: str



class Album(BaseModel):
    artists: list[Artist]
    album_type: str
    id: str
    name: str
    release_date: str
    release_date_precision: str
    total_tracks: int
    uri: str


def get_tracks_from_plages_musicales(sp, input: str):
    print("Parsing plages musicales")
    for line in input.splitlines():
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


def get_tracks_from_stoned_circus(sp, input: str):
    print("Parsing stoned circus")
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
            track = Track(**results["items"][0])
            yield track

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
