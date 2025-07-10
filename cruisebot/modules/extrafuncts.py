import discord
# from discord.ext import commands
from discord.utils import get

def get_mention(context, mention="NULL", debug=False):
    # mention should be a junk string and not None
    if not isinstance(mention, str):
        print(f"{context.author}; ERROR: get_mention param 'mention' requires a string")
        return
    else:
        chars = ['<', '@', '!', '>']
        user_id = ''
        for i in mention:
            if i not in chars:
                user_id += i
        try:
            member = context.guild.get_member(int(user_id))
            return member
        except ValueError as ex: # if None
            if debug == True:
                print(f"get_mention; Member {mention} not found")
            return

def get_user(ctx, str="NULL"):
    # defaults to caller's user if NULL,
    # otherwise passes mention ID to get_mention
    if str == "NULL":
        member = ctx.author
    else:
        member = get_mention(ctx, str)
        if member == None:
            print(f"{ctx.author}; Member not found")
            return None
    return member
