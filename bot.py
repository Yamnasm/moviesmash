from discord.ext import commands
import json, logging, os, sys, util, discord, io, time, random, asyncio

LOGGING_LEVEL = logging.INFO
VOTE_TIMEOUT = 60 * 5
DEV_MODE = False

intents = discord.Intents.default()
intents.members = True

with open("settings.json") as file:
    settings = json.load(file)

bot = commands.Bot(command_prefix=".", pm_help=None, intents=intents)

logging.basicConfig(level=LOGGING_LEVEL, datefmt="%H:%M:%S", format="[%(asctime)s] [%(levelname)8s] >>> %(message)s (%(filename)s:%(lineno)s)",
                    handlers=[logging.FileHandler("latest.log", 'w'), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

ongoing_users = []

@bot.event
async def on_ready():
    logger.info(f"{bot.user.name} has started up ({bot.user.id})")

@bot.event
async def on_message(msg):
    if msg.author.bot or msg.author == bot.user:
        return False

    await bot.process_commands(msg)

@bot.command(name="restart", pass_context=True)
async def restart(ctx):
    if str(ctx.author.id) in ("521807077522407427", "168778575971876864"):
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} invoked .restart command")
        await ctx.send("restarting bot...", delete_after=3)
        await asyncio.sleep(4)
        os.execv(sys.executable, ["python3"] + sys.argv) # restart the bot
    else:
        logger.info(f"{ctx.author.name}#{ctx.author.discriminator} attempted to invoke .restart command")
        await ctx.send(f"{ctx.author.mention} you don't have permission to do that", delete_after=3)

@bot.command(name="test", pass_context=True)
async def test(ctx):
    logger.info(f"{ctx.author.name}#{ctx.author.discriminator} invoked .test command")
    await ctx.send("test")

@bot.command(name="pick", pass_context=True)
async def pick(ctx, log=True, colour=None, validation=False):

    # an attempt to PEP8
    chooser = f"{ctx.author.name}#{ctx.author.discriminator}"

    # checking if the user is already active with the bot
    if ctx.author.id in ongoing_users and not validation:
        logger.info(f"{chooser} attempted to invoke .pick while active")
        await ctx.send(f"✋ {ctx.author.mention} you're already active with me!", delete_after=3)
        await ctx.message.delete()
        return 0
    else:
        ongoing_users.append(ctx.author.id)

	# check if the user is in a dm and this is the first time (that's what log means)
    if log:
        if isinstance(ctx.message.channel, discord.DMChannel):
            logger.info(f"{chooser} invoked .pick command")
        else:
            logger.info(f"{chooser} attempted to invoke .pick while not in a DM")
            return 0

    # keep colours for users
    if not colour:
        logger.debug(f".pick: generated new colour for {chooser}")
        colour = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    else:
        logger.debug(f".pick: {chooser} already has a generated colour")

    check = lambda reaction, user: not user.bot and user == ctx.author and str(reaction.emoji) in ("⬅️", "➡️", "↪️", "🛑")

    choices = util.weighted_movie_pick()

    logger.debug(f".pick ({chooser}): profiling poster downloads...")
    start_time = time.time()

    logger.debug(f".pick ({chooser}): getting posters from choices...")

    poster1 = util.TMDB_IMAGE_URL + util.get_movie_property(choices[0]["id"], "poster_path")
    poster2 = util.TMDB_IMAGE_URL + util.get_movie_property(choices[1]["id"], "poster_path")
    description = f"1. {choices[0]['name']}\n2. {choices[1]['name']}\n"

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

    await msg.add_reaction("⬅️")
    await msg.add_reaction("➡️")
    await msg.add_reaction("↪️")
    await msg.add_reaction("🛑")

    try:
        response = await bot.wait_for("reaction_add", check=check, timeout=VOTE_TIMEOUT)

    except asyncio.TimeoutError:
        ongoing_users.remove(ctx.author.id)
        await msg.delete()
        await ctx.message.delete()
        await ctx.send(f"⏰ {ctx.author.mention} you took too long to decide!", delete_after=3)
        return 0

    if   response[0].emoji == "⬅️":
        logger.info(f".pick ({chooser}): {choices[0]['name']} won against {choices[1]['name']}")
        util.log_result(user=ctx.author.id, winner=choices[0]["id"], loser=choices[1]["id"])

        await msg.delete()
        await pick(ctx, log=False, colour=colour, validation=True)

    elif response[0].emoji == "➡️":
        logger.info(f".pick ({chooser}): {choices[1]['name']} won against {choices[0]['name']}")
        util.log_result(user=ctx.author.id, winner=choices[1]["id"], loser=choices[0]["id"])

        await msg.delete()
        await pick(ctx, log=False, colour=colour, validation=True)

    elif response[0].emoji == "↪️":
        logger.info(f".pick ({chooser}): skipped a vote")
        await msg.delete()
        await pick(ctx, log=False, colour=colour, validation=True)

    elif response[0].emoji == "🛑":
        logger.info(f".pick ({chooser}): stopped requesting choices")
        
        ongoing_users.remove(ctx.author.id)
        await msg.delete()

if __name__ == "__main__":
    if DEV_MODE:
        bot.run(settings["DEV_TOKEN"])
    else:
        bot.run(settings["DISCORD_TOKEN"])
