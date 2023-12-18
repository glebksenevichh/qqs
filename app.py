# Generates quizzes based on a given artist

# import necessary modules
import time
import json
import random
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template

# initialize Flask app
app = Flask(__name__)

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = os.getenv("COOKIE_SECRET")

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

# route to handle logging in
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)
    
# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the quiz_selection route
    return redirect(url_for('quiz_selection',_external=True))

# route to render quiz selection page
@app.route('/quizSelection')
def quiz_selection():
    top_artists = get_top_artists() # get top 5 artists name, id, and image
    return render_template('quiz_select.html', top_artists=top_artists)

#   tbd
#   arguments:
#   id = spotify artist id
@app.route('/quiz/<string:id>')
def quiz(id):
    questions = generate_questions(id)
    return questions

#   converts spotify artist url to artist id
#   arguments:
#   artist_url = spotify artist url
@app.route('/urlToId', methods=['POST'])
def grab_url():
    artist_url = request.form.get('artist_url')
    return artist_url

# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv("CLIENT_ID"),
        client_secret = os.getenv("CLIENT_SECRET"),
        redirect_uri = url_for('redirect_page', _external=True),
        scope='user-top-read '
    )

def get_top_artists():
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # get top 5 artists for user in the last 6 months
    top_artists_data = sp.current_user_top_artists(limit = 5)

    # create dictionary that will be returned 
    top_artists = []

    # iterate over artists and add only name, id, and image to top_artists
    for artist in top_artists_data['items']:
        artist_name = artist['name']
        artist_id = artist['id']    
        # if artist has an image, get the first one
        if (len(artist['images']) != 0):
            artist_image = artist['images'][0]['url']
        else:   # if artist doesn't have an image, return empty string
            artist_image = ''   

        # append artist dictionary to list of top 5
        top_artists.append({
        'name': artist_name,
        'id': artist_id,
        'image': artist_image
        })
    
    return top_artists

def generate_questions(artist_id):
    # Boilerplate Spotify authorization 
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")
    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Get artist data
    artist_info = sp.artist(artist_id)
    albums = sp.artist_albums(artist_id, album_type='album')
    top_tracks = sp.artist_top_tracks(artist_id)
    artist = [artist_info, albums, top_tracks]  # Store all data needed or answers in one artist list

    # Load in questions
    with open('questions.json', 'r') as file:
        questions = json.load(file)

    # Replace artist_questions placeholders
    for artist_question in questions["artist_questions"]:
        artist_name = artist[0]['name']
        artist_question["question"] = artist_question["question"].replace("<artist>", artist_name)
    
    # TODO: Generate correct answers and other answer choices
    generate_artist_answers(artist, questions)
    generate_album_answers(artist, questions)

    return questions

def generate_artist_answers(artist, questions):
    # Iterate over every question in list
    for question in questions['artist_questions']:
        # id of question defines what info we need to pull for our answers
        id = question['id']
        match id:
            case 0: # What genre is <artist> associated with?
                # Get correct answer
                question['answers'][0]['answer'] = artist[0]['genres'][0]

                # Open and load genres list
                with open('genres.json') as f:
                    genres = json.load(f)['music_genres']
                
                # Fill out answer choices with three random genres
                genres = random.sample(genres, 3)   # Select 4 random genres from list
                for answerIndex in range(1, 4):
                    question['answers'][answerIndex]['answer'] = genres[answerIndex-1]

            case 1: # Which is <artist>'s most popular song?
                # Get correct answer
                question['answers'][0]['answer'] = artist[2]['tracks'][0]['name']

                # Fill out answer choices with three other songs
                incorrectChoices = random.sample(range(1, 4), 3)
                for answerIndex in range(1,4):
                    question['answers'][answerIndex]['answer'] = artist[2]['tracks'][incorrectChoices[answerIndex-1]]['name']

            case 2: # Which song by <artist> have you streamed the most?
                # Get correct answer
                print("nothing here yet")

            case 3: # How many albums has <artist> released on Spotify?
                # Get correct answer
                question['answers'][0]['answer'] = artist[1]['total']

                # Generate incorrect answer choices
                num = question['answers'][0]['answer']
                answers_generated = 0
                incorrect_choices = []
                while answers_generated < 4:
                    random_num = random.randint(max(1, num - 2), num + 2)
                    if (random_num != num and random_num not in incorrect_choices):
                        answers_generated = answers_generated + 1
                        incorrect_choices.append(random_num)

                # Fill out answers
                for answerIndex in range(1,4):
                    question['answers'][answerIndex]['answer'] = incorrect_choices[answerIndex-1]

            case 4: # In what year did <artist> release their first album?
                # Get correct answer
                first_album_index = artist[1]['total']
                question['answers'][0]['answer'] = int(artist[1]["items"][first_album_index-1]["release_date"][:4])

                # Generate incorrect answer choices
                num = question['answers'][0]['answer']
                print(num)
                answers_generated = 0
                incorrect_choices = []
                while answers_generated < 4:
                    random_num = random.randint(max(1, num - 2), num + 2)
                    if (random_num != num and random_num not in incorrect_choices):
                        answers_generated = answers_generated + 1
                        incorrect_choices.append(random_num)

                # Fill out answers
                for answerIndex in range(1,4):
                    question['answers'][answerIndex]['answer'] = incorrect_choices[answerIndex-1]
                
            case 5: # Which of the following songs is not in <artist>'s top 10 most-streamed songs on Spotify?
                return
    
    return

def generate_album_answers(artist, questions):
    return

app.run(debug=True)