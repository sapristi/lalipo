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
from lalipo.spotify_helpers import (
    get_tracks_from_plages_musicales, get_tracks_from_stoned_circus, get_tracks_tab_separated,
    get_tracks_simple
)

class InputType(str, Enum):
    simple = "Simple"
    tab_separated = "Tab separated"
    stoned_circus = "Stoned circus"
    plages_musicales = "Plages musicales"

class FirstForm(forms.Form):
    title = forms.CharField(label="Playlist title")
    raw_text = forms.CharField(widget=forms.Textarea)
    input_type = forms.ChoiceField(
        choices=[(v.name, v.value) for v in InputType],
        widget=forms.RadioSelect,
    )
    preview_only = forms.BooleanField(
        help_text="Preview result before creating playlist",
        required=False
    )


# Create your views here.
def input_playlist_view(request):
    form = FirstForm(initial={"input_type": InputType.simple.name})
    return render(request, "gen_playlist.html", {"form": form})


def generate_playlist_view(request):
    form = FirstForm(request.POST)
    if not form.is_valid():
        return HttpResponse(status=400)
    input_type = form.cleaned_data["input_type"]
    title = form.cleaned_data["title"]
    raw_text = form.cleaned_data["raw_text"]
    preview_only = form.cleaned_data["preview_only"]

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
            redirect_uri=settings.HOST,
            scope=scope,
            cache_handler=SparisonCacheHandler(user=request.user),
        )
    )

    match input_type:
        case InputType.simple.name:
            tracks = get_tracks_simple(sp, raw_text)
        case InputType.tab_separated.name:
            tracks = get_tracks_tab_separated(sp, raw_text)
        case InputType.plages_musicales.name:
            tracks = get_tracks_from_plages_musicales(sp, raw_text)
        case InputType.stoned_circus.name:
            tracks = get_tracks_from_stoned_circus(sp, raw_text)
        case _:
            print(f"Could not parse '{input_type}'")
            return HttpResponse(status=400)

    if preview_only:
        if tracks is None:
            tracks = []
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
    return redirect(reverse("input_playlist"))


def preview_playlist_view(request):
    tracks = request.POST["tracks"]

    return render(request, "preview_playlist.html", {"tracks": tracks})


def create_playlist_view(request):
    pass
