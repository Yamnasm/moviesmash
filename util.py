from PIL import Image
import json, time, datetime, random, math, gzip, shutil, os, urllib.request, logging, io

TMDB_API_KEY    = "b9692454ba258237fa4c703f45f7467a"
TMDB_IMAGE_URL  = "https://image.tmdb.org/t/p/w154"
TMDB_MOVIE_URL  = lambda x: f"https://api.themoviedb.org/3/movie/{x}?api_key={TMDB_API_KEY}"

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

def get_random_movie_from_data(data, amount=1):
    return random.sample(data, amount)

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

    with open("history.json", "w") as file:
        json.dump(data, file)