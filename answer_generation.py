import random
import json

def generate_artist_answers(artist, questions):
    # Iterate over every question in list
    for question in questions['artist_questions']:
        # id of question defines what info we need to pull for our answers
        id = question['id']
        match id:
            case 0: # What genre is <artist> associated with?
                # Get correct answer
                question['answers'][0]['answer'] = artist['artist_info']['genres'][0]

                # Open and load genres list
                with open('genres.json') as f:
                    genres = json.load(f)['music_genres']
                
                # Fill out answer choices with three random genres
                genres = random.sample(genres, 3)   # Select 4 random genres from list
                for answerIndex in range(1, 4):
                    question['answers'][answerIndex]['answer'] = genres[answerIndex-1]

            case 1: # Which is <artist>'s most popular song?
                # Get correct answer
                question['answers'][0]['answer'] = artist['top_tracks']['tracks'][0]['name']

                # Fill out answer choices with three other songs
                incorrectChoices = random.sample(range(1, 4), 3)
                for answerIndex in range(1,4):
                    question['answers'][answerIndex]['answer'] = artist['top_tracks']['tracks'][incorrectChoices[answerIndex-1]]['name']

            case 2: # True or False: <artist> is part of 
                # Get correct answer
                print("nothing here yet")

            case 3: # How many albums has <artist> released on Spotify?
                # Get correct answer
                question['answers'][0]['answer'] = artist['albums']['total']

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
                first_album_index = artist['albums']['total']
                question['answers'][0]['answer'] = int(artist['albums']["items"][first_album_index-1]["release_date"][:4])

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
                
            case 5: # Which of these is a real song by <artist>?
                # Get correct answer
                question['answers'][0]['answer'] = random.choice([track['name'] for track in artist['top_tracks']['tracks']])

                # Get 3 random song titles
                with open("song_names.json", 'r') as file:
                    song_names = json.load(file)
                song_names = song_names.get("songs", [])
                random_song_names = random.sample(song_names, 3)

                # Fill out wrong answer choices
                for answerIndex in range (1,4):
                    question['answers'][answerIndex]['answer'] = random_song_names[answerIndex - 1]

    return

def generate_album_answers(artist, questions):
    return