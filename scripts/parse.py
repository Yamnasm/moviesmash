import json, os, sys, inspect, termcolor

# script we need is not in a package???
cd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
pd = os.path.dirname(cd)
sys.path.insert(0, pd)
import util

POPULARITY_MINIMUM = 50

# check for movies we already have so we don't need to parse them
with open("../movies.json") as file:
    existing_movies = json.load(file)

# def progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
#     percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
#     filledLength = int(length * iteration // total)
#     bar = fill * filledLength + '-' * (length - filledLength)
#     print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
#     if iteration == total: 
#         print()

def check_movie(movie):
    if not existing_movies.get(movie['id'], False):
        print(termcolor.colored(f"WE DON'T HAVE THIS MOVIE CATALOGUED!", "green"))
    else:
        print(termcolor.colored("THIS MOVIE ALREADY EXISTS IN OUR DATABASE\n\n\n\n\n", "red"))
        return False

    if movie["popularity"] >= POPULARITY_MINIMUM:
        print(termcolor.colored(f"POPULARITY: {movie['popularity']}", "green"))
    else:
        print(termcolor.colored("THIS MOVIE DOES NOT HAVE A HIGH ENOUGH POPULARITY\n\n\n\n\n", "red"))
        return False

    # since we get original_title we need to get the english title of anything that isn't english by default

    poster = util.get_movie_property(movie.get('id'), "poster_path")

    if poster:
        print(termcolor.colored(f"THIS MOVIE HAS A POSTER PATH!", "green"))
    else:
        print(termcolor.colored("THIS MOVIE DOES NOT HAVE A HIGH ENOUGH POPULARITY\n\n\n\n\n", "red"))
        return False

    return poster

def parse_from_raw():
    with open("movie_dump.json") as file:
        raw_movies = json.load(file)

    with open("../user_movies.json") as file:
        user_movies = json.load(file)
    
    # creates a dictionary instead of a list now for better optimised searching
    movie_dictionary = {}

    # progress_bar(0, len(raw_movies), prefix="Progress", suffix="Complete", length=50)

    for i, movie in enumerate(raw_movies):
        print(f"-- [{i}/{len(raw_movies)}] {movie['id']} --\nTITLE: {movie['title']}")
        poster = check_movie(movie)

        if poster:
            print(termcolor.colored("THIS MOVIE CHECKS ALL BOXES, ADDING TO OUR DATABASE\n\n", "green"))
            
            movie_dictionary[movie['id']] = {
                "id": movie["id"],
                "title": movie["title"],
                "weight": movie["popularity"] - POPULARITY_MINIMUM,
                "poster": poster
            }

        movie_dictionary.update(user_movies)
        os.system("cls") # nice display

        # progress_bar(i + 1, len(raw_movies), prefix="Progress", suffix="Complete", length=50)

    movie_dictionary = dict(sorted(movie_dictionary.items(), key=lambda i:i[1]["weight"]))

    with open("movies.json", "w") as file:
        json.dump(movie_dictionary, file)

if __name__ == "__main__":
    parse_from_raw()