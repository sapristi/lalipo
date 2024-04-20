from enum import Enum
import json

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django import forms
from django.urls import reverse
from django.contrib import messages
from django.utils.safestring import mark_safe

from lalipo.spotify_helpers import (
    get_tracks_from_plages_musicales, get_tracks_from_stoned_circus,
    get_tracks_auto, spotify_app, create_playlist
)

class InputType(str, Enum):
    auto = "Auto"
    stoned_circus = "Stoned circus"
    plages_musicales = "Plages musicales"

class FirstForm(forms.Form):
    title = forms.CharField(label="Playlist title")
    raw_text = forms.CharField(widget=forms.Textarea(attrs={"placeholder": "Ping floyd shine on you\nYom picnic in tchernobyl"}))
    input_type = forms.ChoiceField(
        label="Custom input type",
        choices=[(v.name, v.value) for v in InputType],
        widget=forms.RadioSelect,
    )
    no_preview = forms.BooleanField(
        help_text="Create playlist without preview",
        required=False
    )


def playlist_input_view(request):
    input_type_str = request.GET.get("input_type", "Auto")
    input_type = InputType(input_type_str)
    no_preview_str = request.GET.get("no_preview", "false")
    no_preview = no_preview_str.lower() == "true"
    form = FirstForm(initial={"input_type": input_type.name, "no_preview": no_preview})
    return render(request, "playlist_input.html", {"form": form})


def generate_playlist_view(request):
    form = FirstForm(request.POST)
    if not form.is_valid():
        return HttpResponse(status=400)
    input_type = form.cleaned_data["input_type"]
    title = form.cleaned_data["title"]
    raw_text = form.cleaned_data["raw_text"]
    no_preview = form.cleaned_data["no_preview"]

    sp = spotify_app.for_user(request.user)

    lines : list[str] = [line.strip() for line in raw_text.splitlines() if line]
    match input_type:
        case InputType.auto.name:
            tracks = get_tracks_auto(sp, lines)
        case InputType.plages_musicales.name:
            tracks = get_tracks_from_plages_musicales(sp, lines)
        case InputType.stoned_circus.name:
            tracks = get_tracks_from_stoned_circus(sp, lines)
        case _:
            print(f"Could not parse '{input_type}'")
            return HttpResponse(status=400)

    if not no_preview:
        if tracks is None:
            tracks = []
        tracks = list(tracks)
        print("TRACKS", tracks)

        tracks_json = json.dumps([track.uri for track in tracks])
        return render(request, "preview_playlist.html", {
            "title": title,
            "tracks": tracks,
            "tracks_json": tracks_json,
        })

    playlist = create_playlist(sp, title=title, track_uris=[t.uri for t in tracks])
    print("PLAYLIST", playlist)
    messages.success(request, "Playlist created.")
    return redirect(reverse("input_playlist"))

def preview_playlist_view(request):
    tracks = request.POST["tracks"]
    tracks_json = json.dumps([track.uri for track in tracks])
    print("TRACKS", tracks_json)
    return render(request, "preview_playlist.html", {"tracks": tracks, "tracks_json": tracks_json})

def preview_playlist_test_view(request):
    return render(request, "preview_playlist.html", {"tracks": [
        {"name": "some longer test1", "artists": [{"name": "artist1"}]},
        {"name": "test1", "artists": [{"name": "artist1"}]},
        {"name": "even way longer very very test1", "artists": [{"name": "artist1"}]},
        {"name": "test1", "artists": [{"name": "artist1"}]},
        {"name": "test1", "artists": [{"name": "artist1 with a long name"}]},
        {"name": "test1"*10, "artists": [{"name": "artist1 what if it's so long it goes out"}]},
    ]})


def create_playlist_view(request):

    sp = spotify_app.for_user(request.user)

    tracks = json.loads(request.POST["tracks"])
    title = request.POST["title"]

    playlist = create_playlist(sp, title=title, track_uris=tracks)
    playlist_url = playlist["external_urls"]["spotify"]
    messages.success(
        request, mark_safe(
            f"""Playlist <a href="{playlist_url}" target="_blank">{title}</a> created !"""
        )
    )
    return redirect(reverse("playlist_input"))
