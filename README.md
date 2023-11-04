![banner](./assets/lalipo_banner.png)

# Lalipo - https://lalipo.mmill.eu

Lalipo is made to generate spotify playlists from raw text, for example from this input,

```
Ping floyd shine on you
The doors break on through
Thievery corporation until the morning
Yom picnic in tchernobyl
```

A new playlist will be created in your account:

![playlist](./assets/spotify_test_playlist.png)


# Development

In order to run your own version of Lalipo, you will need to first create a Spotify app: head over to https://developer.spotify.com/dashboard , then create a new app. You will need the client id / client secret for the deployment.

## Deploy - dev server

Lalipo is a standard django app. To deploy locally:

1. Install the dependencies in a virtual env, then activate it.
2. Copy `.env.skeleton` to `.env`, then fill in the values.
2. Run `./manage.py migrate` to apply the migrations.
3. Run `./manage.py runserver` to run the development server.

## Deploy - production

Same for dev server, except that you should run `gunicorn lalipo.wsgi:application` to run the application.

### Systemd + nginx

1. Clone `lalipo` in `/opt/lalipo`
2. Create a virtual environment, and install dependencies:
  - `cd /opt/lalipo`
  - `python -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install .`
3. Copy the systemd unit files in [`assets/systemd`](./assets/systemd):
  - `cp ./assets/systemd/lalipo.service /etc/systemd/system/`
  - `cp ./assets/systemd/lalipo.socket /etc/systemd/system/`
4. Copy `.env.skeleton` to `.env`, and fill the values
5. Proxy requests from nginx, for example with this nginx site configuration:
    ```nginx
    server {
        listen          443 ssl;
        server_name     lalipo.mmill.eu;
        location / {
            include proxy_params;
                proxy_pass http://unix:/run/lalipo-gunicorn.sock;
            }
        ssl_certificate /etc/letsencrypt/live/lalipo.mmill.eu/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/lalipo.mmill.eu/privkey.pem;
    }
    ```
