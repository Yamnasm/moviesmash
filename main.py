import json, time, datetime, random, math, gzip, shutil, os, urllib.request

TMDB_API_KEY    = "b9692454ba258237fa4c703f45f7467a"
TMDB_IMAGE_URL  = "https://image.tmdb.org/t/p/w500"
TMDB_MOVIE_URL  = lambda x: f"https://api.themoviedb.org/3/movie/{x}?api_key={TMDB_API_KEY}"
TMDB_EXPORT_URL = lambda x: f"http://files.tmdb.org/p/exports/movie_ids_{x}.json.gz"

ELO_K_FACTOR = 30

UPDATER_INTERVAL = 0
LAST_UPDATED     = 0

def get_random_movie_from_data(data, amount=1):
    return random.sample(data, amount)

def parse_shitty_json_to_good_json(filename):
    start_time = time.time()

    data = []
    with open(filename, "rb") as file:
        lines = file.readlines()

    for line in lines:
        line = line.decode("utf-8")
        line = json.loads(line)
        data.append(line)
    
    print(f"-- parsing took: {time.time() - start_time:.2f} seconds --")
    return data

def get_latest_tmdb_export():
    # TODO: make it only choose today if it's at or past 8:00 AM UTC
    date     = "10_04_2021" # datetime.date.today().strftime("%m_%d_%Y")
    url      = TMDB_EXPORT_URL(date)
    filename = f"{date}.json.gz"

    # store in downloaded folder place thing
    urllib.request.urlretrieve(url, filename)

    with gzip.open(filename, "rb") as file_in:
        with open(filename[:-3], "wb") as file_out:
            shutil.copyfileobj(file_in, file_out)
    
    os.remove(filename) # cleanup gz zip file
    return filename[:-3] # return name of saved json file

def probability(r1, r2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (r1 - r2) / 400))
  
def elo_rating(w, l):
    w = int(w + ELO_K_FACTOR * (1 - probability(l, w)))
    l = int(l + ELO_K_FACTOR * (0 - probability(w, l)))
    return ((w, l))

def create_choice():
    with open("movies.json", "r") as file:
        data = json.load(file)
        return random.sample(data, 2)

def get_movie_property(movie_id, property):
    url = TMDB_MOVIE_URL(movie_id)
    response = urllib.request.urlopen(url).read().decode("utf-8")
    data = json.loads(response)
    return data[property]

def log_result(user, winner, loser):
    with open("history.json", "r") as file:
        data = json.load(file)
    
    data.append({
        "time"  : int(time.time()),
        "user"  : user,
        "winner": winner,
        "loser" : loser
    })

    with open("results.json", "w") as file:
        json.dump(data, file)

if __name__ == "__main__":
    filename = "10_04_2021.json"
    data     = parse_shitty_json_to_good_json(filename)

    random_movies = get_random_movie_from_data(data, amount=10)

    for movie in random_movies:
        print(f"[{movie['id']}] {movie['original_title']}")