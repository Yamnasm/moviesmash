from discord.ext import commands
import json, logging, os, sys, util, errors, discord, time, random, asyncio, urllib.parse
import urllib.error, termcolor, pathlib, datetime

LOGGING_LEVEL = logging.INFO
VOTE_TIMEOUT = 60 * 5
DEV_MODE = True
LOG_TO_CHANNEL = True

logging.basicConfig(level=LOGGING_LEVEL, datefmt="%H:%M:%S", format="[%(asctime)s] [%(levelname)8s] >>> %(message)s (%(filename)s:%(lineno)s)",
                    handlers=[logging.FileHandler("latest.log", 'w'), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# required settings.json must be readable
try:
    with open("settings.json") as file:
        settings = json.load(file)
except FileNotFoundError:
    logger.error(termcolor.colored(f"!!! THE BOT DOES NOT HAVE SETTINGS.JSON !!!", on_color="on_red"))
    sys.exit()
else:
    logger.info("Found required settings.json")

# required .json files for the bot to function
required_files = ["movies.json", "user_movies.json", "history.json"]
for file in required_files:
    if not pathlib.Path(file).is_file():
        logger.error(termcolor.colored(f"!!! BOT IS MISSING REQUIRED FILE ({file}) !!!", on_color="on_red"))
    else:
        logger.info(f"Found required file: {file}")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=".", pm_help=None, intents=intents)

ongoing_users = []

@bot.event
async def on_ready():
    logger.info(f"{bot.user.name} has started up ({bot.user.id})")

@bot.event
async def on_message(msg):
    if msg.author.bot or msg.author == bot.user:
        return False

    await bot.process_commands(msg)

@bot.event
async def close():
    logger.error(termcolor.colored(f"!!! THE BOT HAS CRASHED !!!", on_color="on_red"))

@bot.command(name="restart", pass_context=True)
async def restart(ctx):
    if not str(ctx.author.id) in ("521807077522407427", "168778575971876864"):
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} attempted to invoke .restart command")
        await ctx.send(f"{ctx.author.mention} you don't have permission to do that", delete_after=3)

    logger.info(f"{ctx.author.name}#{ctx.author.discriminator} invoked .restart command")
    await ctx.send("restarting bot...", delete_after=3)
    await asyncio.sleep(4)
    os.execv(sys.executable, ["python3"] + sys.argv) # restart the bot

@bot.command(name="broadcast", pass_context=True)
async def broadcast(ctx, msg):
    if not str(ctx.author.id) in ("521807077522407427", "168778575971876864"):
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} attempted to invoke .broadcast command")
        await ctx.send(f"{ctx.author.mention} you don't have permission to do that", delete_after=3)

    for user in ongoing_users:
        member = await bot.fetch_user(user)
        await member.send(msg)

@bot.command(name="users", pass_context=True)
async def users(ctx):
    if not str(ctx.author.id) in ("521807077522407427", "168778575971876864"):
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} attempted to invoke .users command")
        await ctx.send(f"{ctx.author.mention} you don't have permission to do that", delete_after=3)
    
    members = [await bot.fetch_user(user) for user in ongoing_users]
    members_name = [f"{member.name}#{member.discriminator}" for member in members]

    if not len(members):
        await ctx.author.send("Nobody is active with me!", delete_after=3)
        return

    message = ""
    for i, name in enumerate(members_name):
        message += f"[{ongoing_users[i]}] {name}\n"

    # don't expose users on a public channel
    await ctx.author.send(message)

@bot.command(name="cancel", pass_context=True)
async def cancel(ctx, user):
    if not str(ctx.author.id) in ("521807077522407427", "168778575971876864"):
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} attempted to invoke .cancel command")
        await ctx.send(f"{ctx.author.mention} you don't have permission to do that", delete_after=3)

    try:
        user = int(user)
    except ValueError:
        return

    if user in ongoing_users:
        logger.info(f".pick ({user}): WAS FORCED TO stop requesting choices")
        ongoing_users.remove(user)
    else:
        await ctx.author.send("That user isn't active with me", delete_after=3)

@bot.command(name="test", pass_context=True)
async def test(ctx):
    logger.info(f"{ctx.author.name}#{ctx.author.discriminator} invoked .test command")
    await ctx.send("test")

@bot.command(name="generate", pass_context=True)
async def generate(ctx):
    if not str(ctx.author.id) in ("521807077522407427", "168778575971876864"):
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} attempted to invoke .generate command")
        await ctx.send(f"{ctx.author.mention} you don't have permission to do that", delete_after=3)
    else:
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} invoked .generate command")
    
    tiered_movies = util.generate_tiered_movies()
    tierlist_file = util.generate_tierlist(tiered_movies)

    # DEBUG
    with open("tierlist.png", "wb") as file:
        file.write(tierlist_file.getbuffer())

    # file = discord.File(tierlist_file, filename="tierlist.png")
    # await ctx.send(file=file)

@bot.command(name="add", pass_context=True)
async def add(ctx, movie):
    logger.info(f"{ctx.author.name}#{ctx.author.discriminator} invoked .add command")

    # validate the movie url (if it is one)
    url = urllib.parse.urlparse(movie)

    if url.scheme and "themoviedb" in url.netloc and url.path:
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} sent a TMDB url, analysing it...")

        movie_id = url.path.split("/")[2].split("-")[0] # get the id at the start of the path after /movie/

        # check if the movie id exists in the... ahem... "database"
        print("CHECKING MOVIE: ", util.get_local_movie_from_id(movie_id))
        if util.get_local_movie_from_id(movie_id):
            logger.info(f"{ctx.author.name}#{ctx.author.discriminator} attempted to add an existing movie!")
            await ctx.send(f"{ctx.author.mention} that movie is already in our database!", delete_after=3)
            await ctx.message.delete()
            return

        try:
            title = util.get_movie_property(movie_id, "title")
            date  = util.get_movie_property(movie_id, "release_date")    

        except errors.MovieNotFound:
            logger.info(f"{ctx.author.name}#{ctx.author.discriminator} gave a TMDB-valid URL but invalid resource.")
            await ctx.send(f"{ctx.author.mention} movie not found (are you sure this is a movie?)", delete_after=3)
            await ctx.message.delete()
            return
            
        else:

            poster = util.get_movie_property(movie_id, "poster_path")

            if not poster:
                logger.info(f"{ctx.author.name}#{ctx.author.discriminator} gave a TMDB-valid URL but it does not have a poster_path.")
                await ctx.send(f"{ctx.author.mention} movie found but it does not have a poster", delete_after=3)
                await ctx.message.delete()
                return

            weight = util.get_movie_property(movie_id, "popularity")
            title = util.get_movie_property(movie_id, "title")
            
            logger.info(f"{ctx.author.name}#{ctx.author.discriminator} added {title} ({date.split('-')[0]})")
            await ctx.send(f"{ctx.author.mention} added {title} ({date.split('-')[0]}) to the user-generated movie list!")
            util.store_user_submitted_movie(movie_id, title=title, weight=weight, poster=poster)
    
    else:
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} sent an invalid url, ignoring...")
        await ctx.send(f"{ctx.author.mention} this isn't a valid themoviedb.org link!", delete_after=3)
        await ctx.message.delete()
        return

@bot.command(name="pick", pass_context=True)
async def pick(ctx, log=True, colour=None, validation=False):

    # an attempt to PEP8
    chooser = f"{ctx.author.name}#{ctx.author.discriminator}"

    # check if the user is in a dm and this is the first time (that's what log means)
    if log:
        if isinstance(ctx.message.channel, discord.DMChannel):
            logger.info(f"{chooser} invoked .pick command")
        else:
            logger.info(f"{chooser} attempted to invoke .pick while not in a DM")
            return

    # checking if the user is already active with the bot
    if ctx.author.id in ongoing_users and not validation:
        logger.info(f"{chooser} attempted to invoke .pick while active")
        await ctx.send(f"??? {ctx.author.mention} you're already active with me!", delete_after=3)
        await ctx.message.delete()
        return

    # user has invoked .pick uniquely
    elif not validation:
        ongoing_users.append(ctx.author.id)

    # keep colours for users
    if not colour:
        logger.debug(f".pick: generated new colour for {chooser}")
        colour = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    else:
        logger.debug(f".pick: {chooser} already has a generated colour")

    check = lambda reaction, user: not user.bot and user == ctx.author and str(reaction.emoji) in ("??????", "??????", "??????", "????")

    # make the choices weighted based on popularity
    choices = util.weighted_movie_pick()

    logger.debug(f".pick ({chooser}): profiling poster downloads...")
    start_time = time.time()

    logger.debug(f".pick ({chooser}): getting posters from choices...")

    poster1 = util.TMDB_IMAGE_URL(154) + util.get_movie_property(choices[0]["id"], "poster_path")
    poster2 = util.TMDB_IMAGE_URL(154) + util.get_movie_property(choices[1]["id"], "poster_path")
    description = f"1. {choices[0]['title']}\n2. {choices[1]['title']}\n"

    embed = discord.Embed(title="- P I C K - A - M O V I E -", description=description, colour=colour)
    embed.set_footer(text=f"{chooser}")

    logger.debug(f".pick ({chooser}): stitching posters together...")
    data = util.convert_posters_to_single_image(poster1, poster2)

    logger.debug(f".pick ({chooser}): uploading bytesio object to discord api...")
    file = discord.File(data, filename="posters.png")

    msg = await ctx.send(file=file, embed=embed)
    logger.debug(f".pick ({chooser}): uploaded bytesio file to discord api!")

    end_time = time.time() - start_time
    logger.debug(f".pick ({chooser}): profiling finished (the routine took {end_time:.2f} seconds)\n")

    await msg.add_reaction("??????")
    await msg.add_reaction("??????")
    await msg.add_reaction("??????")
    await msg.add_reaction("????")

    try:
        response = await bot.wait_for("reaction_add", check=check, timeout=VOTE_TIMEOUT)

    except asyncio.TimeoutError:
        ongoing_users.remove(ctx.author.id)
        await msg.delete()
        await ctx.message.delete()
        await ctx.send(f"??? {ctx.author.mention} you took too long to decide!", delete_after=3)
        return

    if   response[0].emoji == "??????":
        logger.info(f".pick ({chooser}): {choices[0]['title']} won against {choices[1]['title']}")
        util.log_result(
            user_id=ctx.author.id,
            user_name=f"{ctx.author.name}#{ctx.author.discriminator}",
            winner=choices[0]["id"],
            loser=choices[1]["id"]
        )

        if LOG_TO_CHANNEL:
            channel = bot.get_channel(util.LOG_CHANNEL)
            embed = discord.Embed(timestamp=datetime.datetime.utcnow())

            embed.set_thumbnail(url=poster1)
            embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)
            embed.add_field(name=f"{choices[0]['title']} ", value="????", inline=True)
            embed.add_field(name=choices[1]["title"], value="????", inline=True)
            await channel.send(embed=embed)

        await msg.delete()
        await pick(ctx, log=False, colour=colour, validation=True)

    elif response[0].emoji == "??????":
        logger.info(f".pick ({chooser}): {choices[1]['title']} won against {choices[0]['title']}")
        util.log_result(
            user_id=ctx.author.id,
            user_name=f"{ctx.author.name}#{ctx.author.discriminator}",
            winner=choices[1]["id"],
            loser=choices[0]["id"]
        )

        if LOG_TO_CHANNEL:
            channel = bot.get_channel(util.LOG_CHANNEL)
            embed = discord.Embed(timestamp=datetime.datetime.utcnow())

            embed.set_thumbnail(url=poster2)
            embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)
            embed.add_field(name=f"{choices[1]['title']} ", value="????", inline=True)
            embed.add_field(name=choices[0]["title"], value="????", inline=True)
            await channel.send(embed=embed)

        await msg.delete()
        await pick(ctx, log=False, colour=colour, validation=True)

    elif response[0].emoji == "??????":
        logger.info(f".pick ({chooser}): skipped a vote")
        await msg.delete()
        await pick(ctx, log=False, colour=colour, validation=True)

    elif response[0].emoji == "????":
        logger.info(f".pick ({chooser}): stopped requesting choices")
        
        ongoing_users.remove(ctx.author.id)
        await msg.delete()

if __name__ == "__main__":

    try:
        if DEV_MODE:
            bot.run(settings["DEV_TOKEN"])
        else:
            bot.run(settings["DISCORD_TOKEN"])

    finally:
        pass # do final clean up stuff here