import xlsxwriter, datetime, json, discord

def progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    if iteration == total: 
        print()

date = datetime.datetime.now().strftime("%m_%d_%Y")

workbook  = xlsxwriter.Workbook(f"{date}_history.xlsx")
worksheet = workbook.add_worksheet()

cell_format = workbook.add_format({"bold": 1})

row, col = 0, 0

print("Loading history.json contents into memory...")
with open("../history.json") as file:
    history_entries = json.load(file)

# generate titles
worksheet.write(row, col,     "Timestamp",   cell_format)
worksheet.write(row, col + 1, "User ID",     cell_format)
worksheet.write(row, col + 2, "Username",    cell_format)
worksheet.write(row, col + 3, "Winner ID",   cell_format)
worksheet.write(row, col + 4, "Winner Name", cell_format)
worksheet.write(row, col + 5, "Loser ID",    cell_format)
worksheet.write(row, col + 6, "Loser Name",  cell_format)
row += 1

progress_bar(0, len(history_entries), prefix="Progress", suffix="Complete", length=50)

# go through history and append all data to worksheet
# TODO: maybe track the largest object in each column so the width can
#       sized to fit all the text?
for i, entry in enumerate(history_entries):
    time = datetime.datetime.utcfromtimestamp(entry["time"]).strftime("%H:%M:%S, %d/%m/%Y")

    worksheet.write(row, col,     time)
    worksheet.write(row, col + 1, str(entry["user_id"]))
    worksheet.write(row, col + 2, entry["user_name"])
    worksheet.write(row, col + 3, str(entry["winner_id"]))
    worksheet.write(row, col + 4, entry["winner_name"])
    worksheet.write(row, col + 5, str(entry["loser_id"]))
    worksheet.write(row, col + 6, entry["loser_name"])

    row += 1

    progress_bar(i + 1, len(history_entries), prefix="Progress", suffix="Complete", length=50)

workbook.close()