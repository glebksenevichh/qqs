import random
import json
import copy

def fill_out_answers(sp, artist_id):
    # Get artist data
    artist_info = sp.artist(artist_id)
    albums = sp.artist_albums(artist_id, album_type='album')
    top_tracks = sp.artist_top_tracks(artist_id)
    user_top_tracks = sp.current_user_top_tracks(limit=10, time_range='long_term')
    artist = {
        'artist_info': artist_info,
        'albums': albums,
        'top_tracks': top_tracks, 
        'user_top_tracks': user_top_tracks
        }  # Store all data needed or answers in one artist list

    # Load in questions
    with open('json/questions.json') as file:
        questions = json.load(file)

    # Generate answers for all questions
    answers = generate_answers(artist, questions)

    return answers

def generate_answers(artist, questions):
    ''' Takes in artist data and list of questions. Populates list of questions with appropriate answer choices '''
    answers = []

    with open('json/question_answers_templates.json', 'r') as f:
        mc_answers_template = json.load(f)['mc']

    # Iterate over every question in list
    for id in questions['id']:
        question_answers = copy.deepcopy(mc_answers_template)
        # id of question defines what info we need to pull for our answers
        match id:
            case 0: # What genre is <artist> associated with?
                # Get correct answer
                question_answers['answers'][0]['answer'] = artist['artist_info']['genres'][0]

                # Open and load genres list
                with open('json/genres.json') as f:
                    genres = json.load(f)['music_genres']
                
                # Fill out answer choices with three random genres
                genres = random.sample(genres, 3)   # Select 4 random genres from list
                for answerIndex in range(1, 4):
                    question_answers['answers'][answerIndex]['answer'] = genres[answerIndex-1]

            case 1: # Which is <artist>'s most popular song?
                # Get correct answer
                question_answers['answers'][0]['answer'] = artist['top_tracks']['tracks'][0]['name']

                # Fill out answer choices with three other songs
                incorrectChoices = random.sample(range(1, 4), 3)
                for answerIndex in range(1,4):
                    question_answers['answers'][answerIndex]['answer'] = artist['top_tracks']['tracks'][incorrectChoices[answerIndex-1]]['name']

            case 2: # How many albums has <artist> released on Spotify?
                # Get correct answer
                question_answers['answers'][0]['answer'] = artist['albums']['total']

                # Fill out answers
                incorrect_choices = generate_incorrect_nums(question_answers['answers'][0]['answer'])
                for answerIndex in range(1,4):
                    question_answers['answers'][answerIndex]['answer'] = incorrect_choices[answerIndex-1]

            case 3: # In what year did <artist> release their first album?
                # Get correct answer
                first_album_index = artist['albums']['total']
                question_answers['answers'][0]['answer'] = int(artist['albums']["items"][first_album_index-1]["release_date"][:4])

                # Fill out answers
                incorrect_choices = generate_incorrect_nums(question_answers['answers'][0]['answer'])
                for answerIndex in range(1,4):
                    question_answers['answers'][answerIndex]['answer'] = incorrect_choices[answerIndex-1]
                
            case 4: # Which of these is a real song by <artist>?
                # Get correct answer
                question_answers['answers'][0]['answer'] = random.choice([track['name'] for track in artist['top_tracks']['tracks']])

                # Get 3 random song titles
                with open("json/song_names.json", 'r') as file:
                    song_names = json.load(file)
                song_names = random.sample(song_names, 3)

                # Fill out wrong answer choices
                for answerIndex in range (1,4):
                    question_answers['answers'][answerIndex]['answer'] = song_names[answerIndex - 1]

            case 5: # Which of these albums was released first?
                if (len(artist['albums']['items']) > 4):
                    albums = random.sample(list(artist['albums']['items']), 4)

                # Fill out answer options
                question_answers['answers'][0]['answer'] = min(albums[0]['release_date'], 
                                                               albums[1]['release_date'], 
                                                               albums[2]['release_date'],
                                                               albums[3]['release_date'])
                albums.remove(question_answers['answers'][0]['answer'])

                for answerIndex in range(1,4):
                    question_answers['answers'][answerIndex]['answer'] = albums[answerIndex]['name']

            case 6: # Name a song from <album>.
                print("baba booey")

            case 7: # What year did <album> release?
                album = random.choice(list(artist['albums']['items']))

                # Fill out correct answer
                release_year = album.get('release_date').split('-')[0]
                question_answers['answers'][0]['answer'] = int(release_year)

                # Fill out incorrect answer choices
                incorrect_choices = generate_incorrect_nums(question_answers['answers'][0]['answer'])
                for answerIndex in range(1,4):
                    question_answers['answers'][answerIndex]['answer'] = incorrect_choices[answerIndex-1] 
        answers.append(question_answers)

    return answers

def generate_incorrect_nums(num):
    ''' Takes in a number and generates 3 random numbers within a +- 2 range of the argument '''
    answers_generated = 0
    incorrect_choices = []

    # Keep going until 3 numbers are generated
    while answers_generated < 4:
        random_num = random.randint(max(1, num - 2), num + 2)
        # Make sure new number isn't a duplicate of a previously generated one
        if (random_num != num and random_num not in incorrect_choices):
            answers_generated = answers_generated + 1
            incorrect_choices.append(random_num)
    return incorrect_choices