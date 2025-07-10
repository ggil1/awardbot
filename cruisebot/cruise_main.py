import discord
from discord.ext import commands
from discord.utils import get
# from discord import app_commands
from dotenv import load_dotenv
import sqlite3 as sql
import os

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
OWNER = os.getenv('OWNER_ID')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
game_activity = discord.Game(name="Running...")

# change to bot root folder, needed to find things such as cog folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))
bot_home_path = os.getcwd()
print(bot_home_path)

def get_cogs(): # makes a list of cog names within cogs folder
    cog_list = []
    for filename in os.listdir(bot_home_path + "/cogs"):
        if filename.endswith(".py"):
            cog_list.append(filename[:-3])
    return cog_list

bot = commands.Bot(
    command_prefix="c!",
    intents=intents,
    owner_id=OWNER,
    activity=game_activity,
    allowed_mentions=discord.AllowedMentions.none()

)
bot.remove_command('help')
# eventually change these to .env variables, ill get to it eventually lol
bot.admins = [194602590602788865, 337568420067278849]
bot.main_guilds = [348661811287162881, 1346256983140991038]
bot.database = sql.connect("cruise.db")
bot.cursor = bot.database.cursor()

# # process prefixed commands, deprecate?
# @bot.event
# async def on_message(message):
#     try:
#         await bot.process_commands(message) # might break w/ no commands import
#     except Exception as ex:
#         print(ex)

# error handling
@bot.event
async def on_command_error(ctx, error):
    contextmsg = ctx.message.content.split(" ")
    commandname = contextmsg[0]
    if commandname == "": # for slash commands
        commandname = "Command"
    if isinstance(error, commands.CommandNotFound): # don't care about this error
        return
    elif isinstance(error, commands.MissingAnyRole) or isinstance(error, commands.MissingPermissions) or isinstance(error, commands.CheckFailure):
        print(f"{commandname} invoked incorrectly by {ctx.author.name}: {error}")
        await ctx.message.add_reaction("❌")
    else:
        await ctx.send("Error!")
        raise error

@bot.event
async def on_ready():
    print("NS Achievement Bot")
    print(f"{bot.user}\n{bot_home_path}")

    # load cogs from folder
    for c in get_cogs():
        try:
            await bot.load_extension(f"cogs.{c}")
        except discord.ext.commands.errors.ExtensionAlreadyLoaded as ex:
            print(f"Attempted to load cogs.{c} but it was already loaded.")

    # done because it seems like bot cant use get() immediately
    mguilds = []
    for i in bot.main_guilds:
        mguilds.append(get(bot.guilds, id=i))
    # inserting/checking sql info
    print("------ Checking SQL Information ----------")
    curs = bot.cursor
    for g in mguilds:
        for m in g.members:
            if m.bot == False:
                sel = curs.execute("SELECT * FROM UserInfo WHERE ID == (?)", (m.id,))
                lsel = list(sel)
                if not lsel:
                    print(f"Inserting {m} into database..")
                    curs.execute("INSERT INTO UserInfo(ID, NAME) VALUES (?, ?)", (m.id, m.name,))
                    bot.database.commit()
                else:
                    # REMOVE
                    print(f"{m} already in info table")
    print("---------------------------")

# unfinished; now unneeded?
@bot.command()
async def sync(ctx):
    await bot.sync_commands()
    await ctx.send(f"Attempting command sync..")

@bot.command(aliases=["rcog"])
@commands.has_any_role("bareky", "green power")
async def reload_cog(ctx, ext=None):
    try:
        if ext is None:
            print("Enter an extension/cog name.")
            await ctx.send(f"{ctx.author.mention} please input a proper cog name")
        elif ext in get_cogs():
            await bot.reload_extension(f"cogs.{ext}")
            print("Reloading cog.")
            await ctx.channel.purge(limit=1)
        elif ext == "all":
            for extensions in get_cogs():
                await bot.reload_extension(f"cogs.{extensions}")
                print(f"Reloading {extensions}")
                # await ctx.delete()
            await ctx.message.delete()
        else:
            print("Please enter valid cog name.")
            await ctx.send("⚠️")
    except Exception as ex:
        await(ctx.send("Error!"))
        print(ex)

@bot.command()
async def help(ctx):
    if ctx.author.id != 194602590602788865:
        await ctx.send(f"{ctx.author.mention} cmd WIP")
    else:
        await ctx.send(f"```profile, giveaward, removeaward, oldcheck, awardinfo, checkawards, awardlist, featureaward```"
        )

# no more slash commands, atleast not through decorator
# @bot.slash_command(guild_ids=[348661811287162881])
# async def test(ctx):
#     await ctx.respond("testing test")

bot.run(TOKEN)
