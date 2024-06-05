from django.shortcuts import redirect, render
from django.conf import settings
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import json

TOKEN_FILE = 'tokens.json'

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as file:
        json.dump(tokens, file)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as file:
            return json.load(file)
    return None

def get_spotify_client():
    tokens = load_tokens()
    if tokens:
        sp = Spotify(auth=tokens['access_token'])
        try:
            sp.current_user()  # Vérifier si le token est encore valide
            return sp
        except Exception:
            os.remove(TOKEN_FILE)

    auth_manager = SpotifyOAuth(client_id=settings.SPOTIFY_CLIENT_ID,
                                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                                scope=settings.SPOTIFY_SCOPE)
    
    sp = Spotify(auth_manager=auth_manager)
    tokens = {
        'access_token': auth_manager.get_access_token(as_dict=False)
    }
    save_tokens(tokens)
    return sp

def home(request):
    return render(request, 'spotify_integration/home.html')

def spotify_login(request):
    auth_manager = SpotifyOAuth(client_id=settings.SPOTIFY_CLIENT_ID,
                                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                                scope=settings.SPOTIFY_SCOPE)
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

def spotify_callback(request):
    auth_manager = SpotifyOAuth(client_id=settings.SPOTIFY_CLIENT_ID,
                                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                                scope=settings.SPOTIFY_SCOPE)
    
    code = request.GET.get('code')
    tokens = auth_manager.get_access_token(code)
    save_tokens(tokens)
    return redirect('search_track')

def search_track(request):
    sp = get_spotify_client()
    if not sp:
        return redirect('spotify_login')

    if request.method == 'POST':
        track_name = request.POST.get('track_name')
        if not track_name.strip():
            context = {'error': 'Veuillez entrer un nom de piste.'}
            return render(request, 'spotify_integration/search.html', context)

        results = sp.search(q=track_name, type='track', limit=50)  # Augmentez la limite pour plus de résultats à filtrer
        tracks = []
        seen = set()
        for item in results['tracks']['items']:
            triplet = (item['name'], item['artists'][0]['name'], item['album']['name'])
            if triplet not in seen:
                seen.add(triplet)
                track_info = {
                    'name': item['name'],
                    'artist': item['artists'][0]['name'],
                    'artist_image': item['album']['images'][0]['url'] if item['album']['images'] else '',
                    'album': item['album']['name'],
                    'url': item['external_urls']['spotify']
                }
                tracks.append(track_info)

        context = {'tracks': tracks}
        return render(request, 'spotify_integration/search_result.html', context)
    return render(request, 'spotify_integration/search.html')
