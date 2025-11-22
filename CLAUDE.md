# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lalipo is a Django web application that generates Spotify playlists from raw text input. Users can paste song/artist information in various formats, and the app will search Spotify and create a playlist in their account.

## Development Commands

All commands are run with `pdm run` to have the venv available.

### Setup app
```bash
# Install dependencies (use pdm or pip)
pdm install --dev

# Copy environment template and fill in credentials
cp .env.skeleton .env
# Edit .env with your Spotify app credentials from https://developer.spotify.com/dashboard

# Run migrations
pdm run manage.py migrate

# Run development server
pdm run manage.py runserver
```

### Common Management Commands
```bash
# Django shell with IPython (django-extensions installed)
pdm run manage.py shell_plus

# Create superuser for admin access
pdm run manage.py createsuperuser

# Collect static files (production)
pdm run manage.py collectstatic

# Run production server
pdm run gunicorn lalipo.wsgi:application
```

## Architecture

### Authentication Flow
The app uses django-allauth with the Spotify provider to handle OAuth2 authentication. The key integration points:

- **lalipo/spotipy_cache.py**: Contains `SocialAppCacheHandler` and `CustomAuth` classes that bridge django-allauth's token storage (`SocialToken` model) with spotipy's auth system
- **lalipo/spotify_helpers.py**: `SpotifyApp` class initializes Spotify clients using credentials from either the database (`SocialApp` model) or environment variables, creating per-user authenticated clients via `for_user(user)`

### Playlist Generation Pipeline
1. User submits form with title, raw text, and input type (lalipo/views.py:playlist_input_view)
2. Text is parsed into lines and processed based on input type (lalipo/views.py:generate_playlist_view):
   - **auto**: Flexible search - supports tab-separated "artist\ttrack" or free-form search
   - **plages_musicales**: Tab-separated format with album/single distinction
   - **stoned_circus**: Uppercase artist names followed by lowercase track titles
3. Each line is searched via Spotify API (lalipo/spotify_helpers.py:get_tracks_*)
4. Results are either previewed (preview_playlist.html) or directly created as a playlist
5. Playlist creation batches tracks in groups of 100 (Spotify API limit)

### Key Files
- **lalipo/settings.py**: Django configuration with environment-based DEBUG/prod mode toggle
- **lalipo/setup_project.py**: Handles .env loading and paths (BASE_DIR, STATE_DIR for runtime data)
- **lalipo/views.py**: All view logic including form handling and playlist creation
- **lalipo/spotify_helpers.py**: Spotify API interaction, track parsing, and Pydantic models (Track, Artist, Album)
- **lalipo/spotipy_cache.py**: Custom spotipy cache handler that stores tokens in Django's database via django-allauth

### State Management
- Database: SQLite stored in STATE_DIR (runtime/ in dev, configurable in production)
- Static files: Served via WhiteNoise middleware in production
- Spotify tokens: Stored in django-allauth's SocialToken model, automatically refreshed via CustomAuth

### Environment Variables
Required in .env:
- SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET: From Spotify Developer Dashboard
- HOST: Full domain for production (used in redirect URIs)
- DJANGO_SECRET_KEY: Production secret (auto-generated insecure key used in DEBUG mode)
- DEBUG: Set to "true" for development mode

### Template Structure
Uses django-bulma for styling. Key templates:
- templates/playlist_input.html: Main form for text input
- templates/preview_playlist.html: Shows matched tracks before creation (includes embedded Spotify player)
