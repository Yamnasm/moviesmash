import json

def progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    if iteration == total: 
        print()

def parse_from_raw(popularity_min = 50):
    with open("../movie_dump.json") as file:
        raw_movies = json.load(file)

    with open("../user_movies.json") as file:
        user_movies = json.load(file)
    
    # creates a dictionary instead of a list now for better optimised searching
    movie_dictionary = {}

    progress_bar(0, len(raw_movies), prefix="Progress", suffix="Complete", length=50)

    for i, movie in enumerate(raw_movies):

        if movie["popularity"] >= popularity_min and movie["title"][0].isascii():

            movie_dictionary[movie['id']] = {
                "id": movie["id"],
                "title": movie["title"],
                "weight": movie["popularity"] - popularity_min
            }

            movie_dictionary.update(user_movies)

        progress_bar(i + 1, len(raw_movies), prefix="Progress", suffix="Complete", length=50)

    movie_dictionary = dict(sorted(movie_dictionary.items(), key=lambda i:i[1]["weight"]))

    with open("movies.json", "w") as file:
        json.dump(movie_dictionary, file)

if __name__ == "__main__":
    # put this in a file so it can be accessed from multiple places
    POPULARITY_MINIMUM = 50

    parse_from_raw(POPULARITY_MINIMUM)