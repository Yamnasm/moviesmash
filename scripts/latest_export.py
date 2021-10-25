import datetime, urllib.request, shutil, os, gzip

TMDB_EXPORT_URL = lambda x: f"http://files.tmdb.org/p/exports/movie_ids_{x}.json.gz"

date     = "10_25_2021" # datetime.date.today().strftime("%m_%d_%Y")
url      = TMDB_EXPORT_URL(date)
filename = f"{date}.json.gz"

# store in downloaded folder place thing
urllib.request.urlretrieve(url, filename)

with gzip.open(filename, "rb") as file_in:
    with open(filename[:-3], "wb") as file_out:
        shutil.copyfileobj(file_in, file_out)

os.remove(filename) # cleanup gz zip file
print(filename[:-3]) # return name of saved json file