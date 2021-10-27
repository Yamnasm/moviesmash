from PIL import Image
import json, time, random, math, urllib.request, logging, io, errors

TMDB_API_KEY    = "b9692454ba258237fa4c703f45f7467a"
TMDB_IMAGE_URL  = "https://image.tmdb.org/t/p/w154"
TMDB_MOVIE_URL  = lambda x: f"https://api.themoviedb.org/3/movie/{x}?api_key={TMDB_API_KEY}"

# put this in a file so it can be accessed from multiple places
MINIMUM_MOVIE_POPULARITY = 50

ELO_K_FACTOR = 30

UPDATER_INTERVAL = 0
LAST_UPDATED     = 0

logger = logging.getLogger(__name__)

def convert_posters_to_single_image(poster1, poster2):
    logger.debug(f"convert_posters_to_single_image: received url ({poster1})")
    logger.debug(f"convert_posters_to_single_image: received url ({poster2})")
    im1 = Image.open(urllib.request.urlopen(poster1))
    im2 = Image.open(urllib.request.urlopen(poster2))

    logger.debug("convert_posters_to_single_image: creating new image and pasting posters")
    dst = Image.new("RGB", (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))

    logger.debug("convert_posters_to_single_image: creating bytesio file and saving image data")
    output = io.BytesIO()
    dst.save(output, format="PNG")

    logger.debug("convert_posters_to_single_image: setting seek to zero for bytesio object")
    output.seek(0)
    return output

def get_random_movie_from_data(movies):
    choices = random.sample(list(movies.keys()), 2)

    # prevents giving the user the same movie
    if choices[0]["id"] == choices[1]["id"]:
        return get_random_movie_from_data(movies)
    else:
        return choices

def get_local_movie_from_id(id):
    with open("movies.json", "r") as file:
        movies = json.load(file)

    return movies.get(str(id), False)

def weighted_movie_pick():
    def iterate_comparison(rt, ti):
        rand = rt * random.random()
        low = 0
        high = len(ti)

        while low < high:
            mid = low + (high - low) // 2
            if rand > ti[mid]:
                low = mid + 1
            else:
                high = mid
        return low

    total_index = []
    running_total = 0

    with open("movies.json", "r") as file:
        movies = json.load(file)
        movielist = []
        for key, movie in movies.items():
            movielist.append(movie)

        for w in movielist:
            running_total += w["weight"]
            total_index.append(running_total)

        return [movielist[iterate_comparison(running_total, total_index)] for _ in range(2)]

def probability(r1, r2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (r1 - r2) / 400))

def elo_rating(w, l):
    w = int(w + ELO_K_FACTOR * (1 - probability(l, w)))
    l = int(l + ELO_K_FACTOR * (0 - probability(w, l)))
    return ((w, l))

def create_choice():
    with open("movies.json", "r") as file:
        movies = json.load(file)
        return random.sample(movies, 2)

def get_movie_property(movie_id, property):
    url = TMDB_MOVIE_URL(movie_id)

    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        logger.info(f"Received a {e.code} from get_movie_property: e")
        logger.info(f"could not get 200 code from get_movie_property url request")
        raise errors.MovieNotFound(e.code, "Movie not found")
    else:
        response_content = response.read().decode("utf-8")
        movies = json.loads(response_content)

        return movies[property]

def store_user_submitted_movie(movie_id, title):
    with open("user_movies.json", "r") as file:
        data = json.load(file)

    data[movie_id] = {
        "name": title,                                       # this can go into the negative???
        "weight": get_movie_property(movie_id, "popularity") # - MINIMUM_MOVIE_POPULARITY
    }

def log_result(user, winner, loser):
    with open("history.json", "r") as file:
        movies = json.load(file)
    
    movies.append({
        "time"  : int(time.time()),
        "user"  : user,
        "winner": winner,
        "loser" : loser
    })

    with open("history.json", "w") as file:
        json.dump(movies, file)