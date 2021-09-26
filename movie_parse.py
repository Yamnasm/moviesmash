import json

# this file wil contain all of the other parsing things too.

def parse_from_raw(popularity_min = 50):
    with open("movie_dump.json") as file:
        raw_movies = json.load(file)
        movie_dictionary = []
        for movie in raw_movies:
            if movie["popularity"] >= popularity_min:
                if movie["original_title"][0].isascii():
                    movie_dictionary.append({
                        "id": movie["id"],
                        "name": movie["original_title"],
                    })
        
        with open("movies.json", "w") as file:
            json.dump(movie_dictionary, file)

if __name__ == "__main__":
    POPULARITY_MINIMUM = 50
    parse_from_raw(POPULARITY_MINIMUM)
