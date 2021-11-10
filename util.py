from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps
import json, time, random, urllib.request, logging, io, errors, requests, math, bot, process_elo

TMDB_API_KEY    = "b9692454ba258237fa4c703f45f7467a"
TMDB_IMAGE_URL  = lambda x: f"https://image.tmdb.org/t/p/w{x}" # 92, 154, 185, 342, 500, 780, original
TMDB_MOVIE_URL  = lambda x: f"https://api.themoviedb.org/3/movie/{x}?api_key={TMDB_API_KEY}"

# put this in a file so it can be accessed from multiple places
MINIMUM_MOVIE_POPULARITY = 50

UPDATER_INTERVAL = 0
LAST_UPDATED     = 0

# changes the log channel depending on if it's DEV_MODE or not
LOG_CHANNEL = 903446384932446299 if bot.DEV_MODE else 905216536057376808

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
    {"text": "F"  , "colour": "#7f7fff"}
]

logger = logging.getLogger(__name__)

def get_local_movie_from_id(id):
    with open("movies.json", "r") as file:
        movies = json.load(file)

    return movies.get(str(id), False)

def generate_tiered_movies():
    ranked_movies = process_elo.process_history()
    ranked_movies = sorted(ranked_movies, key=lambda x: x["elo"], reverse=True)

    maximum_elo = ranked_movies[0]["elo"]
    minimum_elo = ranked_movies[-1]["elo"]
    threshold = (maximum_elo - minimum_elo) // 9 # 9 is the amount of tiers in our tierlist
    tiered_movies = [[], [], [], [], [], [], [], [], []]

    for movie in ranked_movies:
        elo = movie["elo"]

        if   maximum_elo == elo > (threshold * 8) + minimum_elo:
            tiered_movies[0].append(movie)
        elif (threshold * 8) + minimum_elo < elo > (threshold * 7) + minimum_elo:
            tiered_movies[1].append(movie)
        elif (threshold * 7) + minimum_elo < elo > (threshold * 6) + minimum_elo:
            tiered_movies[2].append(movie)
        elif (threshold * 6) + minimum_elo < elo > (threshold * 5) + minimum_elo:
            tiered_movies[3].append(movie)
        elif (threshold * 5) + minimum_elo < elo > (threshold * 4) + minimum_elo:
            tiered_movies[4].append(movie)
        elif (threshold * 4) + minimum_elo < elo > (threshold * 3 + minimum_elo):
            tiered_movies[5].append(movie)
        elif (threshold * 3) + minimum_elo < elo > (threshold * 2) + minimum_elo:
            tiered_movies[6].append(movie)
        elif (threshold * 2) + minimum_elo < elo > (threshold * 1) + minimum_elo:
            tiered_movies[7].append(movie)
        elif threshold + minimum_elo < elo > minimum_elo:
            tiered_movies[8].append(movie) 

    # DEBUG
    # print("THRESHOLDS: F     E     D     C     B     A     S     S+    SS+")
    # print("THRESHOLDS:", minimum_elo, [(threshold * i) + minimum_elo for i in range(1, 8)], maximum_elo)

    # with open("tiered.json", "w") as file:
    #     json.dump(tiered_movies, file)

    return tiered_movies

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
                    movie_id = movies[processed_movies]["movie_id"]
                    movie = get_local_movie_from_id(movie_id)
                    poster = TMDB_IMAGE_URL(92) + movie["poster"]

                    r = requests.get(poster, stream=True)

                    if not r.status_code == 200:
                        raise Exception(f"Didn't receive a 200 OK on downloading {poster}")
                    
                    # DEBUG
                    # print(f"{get_movie_property(movie_id, 'title')} placed {text}")

                    image = Image.open(io.BytesIO(r.content))

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

def get_movie_property(movie_id, property):
    url = TMDB_MOVIE_URL(movie_id)

    try:
        response = requests.get(url)
    except requests.exceptions.HTTPError as e:
        logger.info(f"Received a {e.code} from get_movie_property: e")
        logger.info(f"could not get 200 code from get_movie_property url request")
        raise errors.MovieNotFound(e.code, "Movie not found")
    else:
        movies = response.json()

        return movies[property]

def store_user_submitted_movie(movie_id, title, weight, poster):
    with open("user_movies.json") as file:
        data = json.load(file)

    data[movie_id] = {
        "name": title,    # this can go into the negative???
        "weight": weight, # - MINIMUM_MOVIE_POPULARITY
        "poster": poster
    }

    with open("user_movies.json", "w") as file:
        json.dump(data, file)

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