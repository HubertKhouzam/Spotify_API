import spotipy

import time

from spotipy.oauth2 import SpotifyOAuth

from flask import Flask, request, url_for, session, redirect

#initialise Flask app
app = Flask(__name__)

#Setting up cookie for session
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'jfie@*sj484324@3483##84'
TOKEN_INFO = 'token_info'

# asking spotify for autorisation
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

# get token to get session
@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_discover_weekly', external = True))


# main function to save new playlist and fill it 
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    # get token
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect('/')
    

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']
    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None

    # check in users playlist to find Discover Weekly and if Saved weekly exists
    current_playlists = sp.current_user_playlists(limit=50)['items']
    for playlist in current_playlists:
        if(playlist['name'] == "Discover Weekly"):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == "Saved Weekly"):
            saved_weekly_playlist_id = playlist['id']

    # edge case + create  playlist if necessary
    if not discover_weekly_playlist_id:
        return 'Discover Weekly playlist not found'
    
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    # get songs from discover playlist and adding them to new playlist 
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    
    
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)
    return 'Success'



def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))

    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info



# random stuff to create session
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id='e2eee8564b6943df8cc30b6ac6bc18f6',
        client_secret='e603d91ada324e7e8c13a3f25aeb85e6',
        redirect_uri= url_for('redirect_page', _external= True), 
        scope='user-library-read playlist-read-private playlist-modify-public playlist-modify-private'
        )

# IMPORTANT to run app flask
app.run(debug=True)