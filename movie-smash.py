import json, random, math, urllib.request, urllib.parse, os
from datetime import datetime

def present():
    with open("movies.json", "r") as file:
        data = json.load(file)
        choices = random.sample(data, 2)
        return choices

def record_result(choice, user):
    winner = choice[0]["id"]
    loser = choice[1]["id"]

    the_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    new_data = {
        "winner": winner,
        "loser": loser,
        "user": user,
        "time": the_time
    }
    a = []
    if not os.path.isfile("results.json"):
        a.append(new_data)
        with open("results.json", mode='w') as f:
            f.write(json.dumps(a, indent=2))
    else:
        with open("results.json", "r+") as file:
            data = json.load(file)
            data.append(new_data)
            file.seek(0)
            json.dump(data, file)

def probability(rating1, rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))
  
def elo_rating(winner, loser):
    K = 30
    winner = int(winner + K * (1 - probability(loser, winner)))
    loser = int(loser + K * (0 - probability(winner, loser)))
    return((winner, loser))

def get_movie_poster(movie_id, api_token):
    TMDB_MOVIE_URL = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_token}"
    TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

    response = urllib.request.urlopen(TMDB_MOVIE_URL).read().decode("utf-8")
    data = json.loads(response)
    return TMDB_IMAGE_URL + data["poster_path"]

if __name__ == "__main__":

    with open("settings.json") as settings:
        sett = json.load(settings)
        api_key = sett["TMDB_API_KEY"]

    # just a CLI function
    def decide(choices):
        pick = input(f"1: {choices[0]['name']}\n2: {choices[1]['name']}\n")
        if pick == "1":
            return choices
        else:
            choices[0], choices[1] = choices[1], choices[0]
            return choices

    choices = present()
    record_result(decide(choices), "COMMANDLINE")

    #example of movie_poster usage.
    print(get_movie_poster(choices[0]["id"], api_key))