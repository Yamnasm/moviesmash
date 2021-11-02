from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps
import json, time, random, math, urllib.request, logging, io, errors, requests, math

TMDB_API_KEY    = "b9692454ba258237fa4c703f45f7467a"
TMDB_IMAGE_URL  = "https://image.tmdb.org/t/p/w154"
TMDB_MOVIE_URL  = lambda x: f"https://api.themoviedb.org/3/movie/{x}?api_key={TMDB_API_KEY}"

# put this in a file so it can be accessed from multiple places
MINIMUM_MOVIE_POPULARITY = 50

ELO_K_FACTOR = 30

UPDATER_INTERVAL = 0
LAST_UPDATED     = 0

LOG_CHANNEL      = 903446384932446299

TIERLIST_MAX_COLUMNS_ALLOWED = 50
TIERLIST_PADDING_PIXELS = (10, 10, 10, 10)
TIERLIST_FONT_FAMILY    = "arial.ttf"
TIERLIST_POSTER_WIDTH   = 92
TIERLIST_POSTER_HEIGHT  = 138
TIERLIST_FONTSIZE       = 50 # pixels
TIERLIST_CATEGORIES     = [
    {"text": "SS+", "colour": "#ff7f7f"},
    {"text": "S+" , "colour": "#ffbf7f"},
    {"text": "S"  , "colour": "#ffdf7f"},
    {"text": "A"  , "colour": "#ffff7f"},
    {"text": "B"  , "colour": "#bfff7f"},
    {"text": "C"  , "colour": "#7fff7f"},
    {"text": "D"  , "colour": "#7fffff"},
    {"text": "E"  , "colour": "#7fbfff"},
    {"text": "F"  , "colour": "#7f7fff"},
    {"text": "?"  , "colour": "#ff7fff"}
]

logger = logging.getLogger(__name__)

def generate_tierlist(tiered_movies):

    # this is so we can loop through them all and stitch them together
    tier_images = []

    for i, movies in enumerate(tiered_movies):

        text   = TIERLIST_CATEGORIES[i].get('text')
        colour = ImageColor.getrgb(TIERLIST_CATEGORIES[i].get('colour'))
        label  = Image.new("RGB", (TIERLIST_POSTER_WIDTH, TIERLIST_POSTER_HEIGHT), colour)
        font   = ImageFont.truetype(TIERLIST_FONT_FAMILY, TIERLIST_FONTSIZE)

        text_width, text_height = font.getsize(text)
        text_position = ( (TIERLIST_POSTER_WIDTH - text_width) / 2, (TIERLIST_POSTER_HEIGHT - text_height) / 2 )
        ImageDraw.Draw(label).text(text_position, text, fill="white", font=font)

        # creates the starting image that has all the movie posters appended to but first
        # we need to paste the tierlist label onto it
        start_image = Image.new("RGB", (TIERLIST_POSTER_WIDTH * 2, TIERLIST_POSTER_HEIGHT), colour)
        start_image.paste(label, (0, 0))

        processed_movies = 0
        row = 0

        # get the correct width and height for the tierlist
        max_width  = min(TIERLIST_POSTER_WIDTH, max(len(movies) for movies in tiered_movies)) * TIERLIST_MAX_COLUMNS_ALLOWED
        max_height = TIERLIST_POSTER_HEIGHT * math.ceil(len(movies) / TIERLIST_MAX_COLUMNS_ALLOWED)

        while not processed_movies == len(movies):
            col = 1 # start at one so the label is on it's own column

            while not col == TIERLIST_MAX_COLUMNS_ALLOWED:
                
                # stop processing if we run out of movies to append
                try:
                    image = movies[processed_movies]
                except IndexError:
                    break
                
                # NOTE: this could maybe be more efficient? maybe we don't need two pastes
                destination = Image.new("RGB", (max_width, max_height), colour)
                destination.paste(start_image, (0, 0))
                destination.paste(image, (TIERLIST_POSTER_WIDTH * col, TIERLIST_POSTER_HEIGHT * row))

                start_image = destination
                col += 1
                processed_movies += 1
            
            row += 1
        
        final_image = ImageOps.expand(start_image, TIERLIST_PADDING_PIXELS, colour)
        tier_images.append(final_image)
    
    # get the largest width in the tierlist and the combined height of all the images
    max_width  = max(image.width for image in tier_images)
    max_height = sum(image.height for image in tier_images)

    # stitch together all the generated tier images
    start_image = Image.new("RGB", (max_width, max_height))
    height = 0

    for image in tier_images:
        start_image.paste(image, (0, height))
        height += image.height
    
    output = io.BytesIO()
    start_image.save(output, format="PNG")
    output.seek(0)

    return output


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

# def get_random_movie_from_data(movies):
#     choices = random.sample(list(movies.keys()), 2)

#     # prevents giving the user the same movie
#     if choices[0]["id"] == choices[1]["id"]:
#         return get_random_movie_from_data(movies)
#     else:
#         return choices

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
        choices = [movielist[iterate_comparison(running_total, total_index)] for _ in range(2)]
        if choices[0]["id"] == choices[1]["id"]:
            return weighted_movie_pick()
        else:
            return choices

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

def log_result(user_id, user_name, winner, loser):
    with open("history.json", "r") as file:
        movies = json.load(file)
    
    # maybe in future add the weight to the history
    # since the xlsx shit is gonna see it and you
    # might want to do some funky stuff with that?
    movies.append({
        "time"        : int(time.time()),
        "user_id"     : user_id,
        "user_name"   : user_name,
        "winner_id"   : winner,
        "winner_name" : get_movie_property(winner, "title"),
        "loser_id"    : loser,
        "loser_name"  : get_movie_property(loser, "title")
    })

    with open("history.json", "w") as file:
        json.dump(movies, file)