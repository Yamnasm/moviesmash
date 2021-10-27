import json, sys, datetime

def progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    if iteration == total: 
        print()

date = datetime.date.today()

# 8:00AM UTC means it's the next day for an export
if not datetime.datetime.now().hour > 8:
    date -= datetime.timedelta(days=1)

date = date.strftime("%m_%d_%Y")

with open(f"{date}.json", encoding="utf-8") as file:
    lines = file.readlines()

movies = []
progress_bar(0, len(lines), prefix="Progress", suffix="Complete", length=50)

try:
    for i, line in enumerate(lines):
        data = json.loads(line)
        movies.append({
            "id": data["id"],
            "title": data["original_title"],
            "popularity": data["popularity"]
        })

        progress_bar(i + 1, len(lines), prefix="Progress", suffix="Complete", length=50)

except KeyboardInterrupt:
    print("KILLED BY KEYBOARD")
    sys.exit()

with open("movie_dump.json", "w") as file:
    json.dump(movies, file)