import discord
from discord.ext import commands
import modules.extrafuncts as extra

class Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        print("Profiles cog has loaded.")


    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot == True: return
        curs = self.bot.cursor
        sel = curs.execute("SELECT * FROM UserInfo WHERE ID == (?)", (msg.author.id,))
        lsel = list(sel)
        if not lsel:
            # user not in db, add late
            curs.execute("INSERT INTO Userinfo(ID, NAME) VALUES (?, ?)", (msg.author.id, msg.author.name))
            self.bot.database.commit()
            print(f"* {msg.author} lateadded to database")
        else:
            # user already in db
            return

    def retr_awards(ctx, m, embed):
        # function responsible for making award string for profiles
        con = ctx.bot.database
        curs = ctx.bot.cursor

        awards = list(curs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (m.id,)))
        try:
            awards = awards[0][0] # access list then tuple [()]
        except IndexError as ex:
            print(f"{ctx.author}, {m}, retr_awards; Member has no awards")
            return

        awardspl = awards.split(",")
        awardspl_l = []
        awardtext = ""
        for a in awardspl: # remove date from every award, add awardname to list
            aspl = a.split("/")
            try:
                aspl[2]
            except IndexError as ex:
                print(f"caller: {ctx.author}; No feature info for award {aspl[0]}")
                continue
            if aspl[2] == "F":
                awardspl_l.append(aspl[0])
        # now award names are in awardspl_l
        print(awardspl_l)
        c = 0
        for n in awardspl_l:
            # print(n)
            c += 1
            if n:
                awardname = curs.execute("SELECT DISPNAME FROM AwardInfo WHERE NAME == (?)", (n,))
                awardname = list(awardname)[0][0]
                awardemoji = curs.execute("SELECT EMOJI FROM AwardInfo WHERE NAME == (?)", (n,))
                awardemoji = list(awardemoji)[0][0]
                if c == 1:
                    awardtext = f"{awardemoji} {awardname}"
                elif c <= 20:
                    awardtext += f", {awardemoji} {awardname}"
                # else:
                #     awardtext += ", ..." # use to make limit how many awards show
                #     break

        # print(awardtext)
        # c -= 1 # c seems to always be off by 1, think its because of a null award
        # null award issue might be fixed with award features
        embed.add_field(name=f"Featured Awards [{c}]", value=awardtext, inline=False)
        return embed



    @commands.command()
    async def profile(self, ctx, mention="NULL"):
        member = None
        if mention == "NULL":
            member = ctx.author
        else:
            member = extra.get_mention(ctx, mention)
        if member == None: return
        masterycount = 0
        for r in member.roles:
             if "Mastery" in r.name:
                 for l in r.name:
                     if l == "★":
                         masterycount += 1
        prof_embed = discord.Embed(
            title=f"{member.display_name}'s Profile", # might use member.name
            description=f"*{member.name}*\n**Mastery Level:** {masterycount}",
            color=member.color
        )
        if masterycount == 4:
            prof_embed.description = f"*{member.name}*\n***Mastery Level:** *{masterycount}*"
        elif masterycount == 5:
            prof_embed.description = f"*{member.name}*\n***Mastery Level:*** ***{masterycount} :star:***"
        elif ctx.guild.id != 1346256983140991038:
            prof_embed.description = f"*{member.name}*"
        join_str = member.joined_at.strftime("%b. %d, %Y")
        create_str = member.created_at.strftime("%b. %d, %Y")

        prof_embed.set_thumbnail(url=member.avatar)
        # prof_embed.add_field(name="Mastery Level", value=f"{masterycount}", inline=False)
        prof_embed.add_field(name="Join Date", value=f"{join_str}", inline=True)
        prof_embed.add_field(name="Creation Date", value=f"{create_str}", inline=True)

        # mostly errors because of no award info
        # if this errors then you just get a profile with no awards on it
        try:
            Profiles.retr_awards(ctx, member, prof_embed)
        except Exception as ex:
            print(f"Error when searching for {member} awards: {ex}")

        await ctx.send(embed=prof_embed)



async def setup(bot):
    await bot.add_cog(Profiles(bot))
