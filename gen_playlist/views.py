from django.shortcuts import render
from .forms import FirstForm

# Create your views here.
def gen_playlist_view(request):

    form = FirstForm()

    return render(request, "gen_playlist.html", {"form": form})
