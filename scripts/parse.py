import json

def progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    if iteration == total: 
        print()

def parse_from_raw(popularity_min = 50):
    with open("movie_dump.json") as file:
        raw_movies = json.load(file)

    movie_dictionary = []

    progress_bar(0, len(raw_movies), prefix="Progress", suffix="Complete", length=50)

    for i, movie in enumerate(raw_movies):

        if movie["popularity"] >= popularity_min:
            if movie["original_title"][0].isascii():
                movie_dictionary.append({
                    "id": movie["id"],
                    "name": movie["original_title"],
                    "weight": movie["popularity"] - popularity_min
                })
        
        progress_bar(i + 1, len(raw_movies), prefix="Progress", suffix="Complete", length=50)

    movie_dictionary.sort(key = lambda x:x["weight"])
    with open("movies.json", "w") as file:
        json.dump(movie_dictionary, file)

if __name__ == "__main__":
    POPULARITY_MINIMUM = 50
    parse_from_raw(POPULARITY_MINIMUM)