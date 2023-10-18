from django.http import HttpResponse
from django.shortcuts import redirect, render
from django import forms
from django.conf import settings
from enum import Enum
from allauth.socialaccount.models import SocialApp
import itertools
from django.urls import reverse

from spotipy import Spotify

from lalipo.spotipy_cache import SparisonCacheHandler, CustomAuth
from lalipo.logic import get_tracks_from_plages_musicales, get_tracks_from_stoned_circus


class InputType(str, Enum):
    stoned_circus = "stoned circus"
    plages_musicales = "plages musicales"

class FirstForm(forms.Form):
    title = forms.CharField()
    raw_text = forms.CharField(widget=forms.Textarea)
    input_type = forms.ChoiceField(
        choices=[(v.name, v.value) for v in InputType],
        widget=forms.RadioSelect
    )
    preview = forms.BooleanField(
        help_text="Preview result before creating playlist",
        required=False
    )


# Create your views here.
def input_playlist_view(request):
    form = FirstForm()
    return render(request, "gen_playlist.html", {"form": form})


def generate_playlist_view(request):
    title = request.POST["title"]
    raw_text = request.POST["raw_text"]
    input_type = request.POST["input_type"]
    preview = "preview" in request.POST
    print("PARAMS", request.POST)
    spotify_app = SocialApp.objects.first()

    if spotify_app:
        client_id=spotify_app.client_id
        client_secret=spotify_app.secret
        scope=spotify_app.settings["SCOPE"]
    else:
        client_id = settings.SOCIALACCOUNT_PROVIDERS["spotify"]["APP"]["client_id"]
        client_secret = settings.SOCIALACCOUNT_PROVIDERS["spotify"]["APP"]["secret"]
        scope=settings.SOCIALACCOUNT_PROVIDERS["spotify"]["SCOPE"]

    sp = Spotify(
        client_credentials_manager=CustomAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://localhost:8000",
            scope=scope,
            cache_handler=SparisonCacheHandler(user=request.user),
        )
    )

    if input_type == InputType.plages_musicales.name:
        tracks = get_tracks_from_plages_musicales(sp, raw_text)
    else:
        tracks = get_tracks_from_stoned_circus(sp, raw_text)

    if preview:
        tracks = list(tracks)
        print("TRACKS", tracks)

        return render(request, "preview_playlist.html", {"tracks": tracks})

    playlist = sp.user_playlist_create(
        user=sp.current_user()["id"],
        name=title
    )
    print("MADE playlist", playlist)

    while True:
        tracks_batch = list(itertools.islice(tracks, 100))
        if len(tracks_batch) == 0:
            break
        sp.playlist_add_items(
            playlist_id=playlist["id"],
            items=[t.uri for t in tracks_batch]
        )
    return redirect(reverse("generate_playlist"))


def preview_playlist_view(request):
    tracks = request.POST["tracks"]

    return render(request, "preview_playlist.html", {"tracks": tracks})


def create_playlist_view(request):
    pass
