import math, json

ELO_K_FACTOR = 30

def probability(r1, r2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (r1 - r2) / 400))

def calculate_elo(matchup):
    w = matchup[0]
    l = matchup[1]
    w = int(w + ELO_K_FACTOR * (1 - probability(l, w)))
    l = int(l + ELO_K_FACTOR * (0 - probability(w, l)))
    return ((w, l))

def process_history():
    def add_movie_if_new(dic_list, key):
        for d in dic_list:
            if key == d["movie_id"]:
                return dic_list
        elo_ratings.append({"movie_id": key, "elo": 1500})
        return dic_list

    elo_ratings = []
    with open("history.json", "r") as file:
        history = json.load(file)
    for match in history:

        # movie might not exist, so this is sortof necessary
        elo_ratings = add_movie_if_new(elo_ratings, match["winner_id"])
        elo_ratings = add_movie_if_new(elo_ratings, match["loser_id"])
        
        # acquiring elo of each movie
        elo_matchup = []
        for d in elo_ratings:
            if d["movie_id"] == match["winner_id"]:
                elo_matchup.append(d["elo"])
        for d in elo_ratings:
            if d["movie_id"] == match["loser_id"]:
                elo_matchup.append(d["elo"])

        # process elo
        elo_matchup = calculate_elo(elo_matchup)

        # dump new-elo back into list
        for d in elo_ratings:
            if d["movie_id"] == match["winner_id"]:
                d["elo"] = elo_matchup[0]
        for d in elo_ratings:
            if d["movie_id"] == match["loser_id"]:
                d["elo"] = elo_matchup[1]

    return elo_ratings
    
if __name__ == "__main__":
    print(process_history())