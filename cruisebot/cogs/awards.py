import discord
from discord.ext import commands
import modules.extrafuncts as extra
from datetime import datetime


class Awards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # async def cog_check(self, ctx):
    #     return ctx.author.id in ctx.bot.admins # admin only cog?

    def match_award(cn, crs, a_name, u):
        """
        Makes sure that passed in award name matches with an award from
        user's award list.
        a_name = award name
        u = user
        cn, crs = SQL
        Returns debug name of award if success, otherwise returns None
        """

        name = None
        db_award = crs.execute("SELECT * FROM AwardInfo WHERE DISPNAME == (?)", (a_name,))
        try:
            debug_name = list(db_award)[0][1]
        except IndexError as ex:
            return None

        u_awards = crs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (u.id,))
        ustring = list(u_awards)[0][0] # access award string
        u_awards_spl = ustring.split(",")

        # would be more efficient if using debug names,
        # but due to using display names it has to loop through every user award
        for a in u_awards_spl:
            aspl = a.split("/") # seperate award attributes, debug name is first
            if debug_name == aspl[0]:
                name = debug_name

        return name

    async def ga_funct(ctx, cn, crs, a, memb):
        userinfo = list(crs.execute("SELECT * FROM UserInfo WHERE ID == (?)", (memb.id,)))
        if not userinfo:
            await ctx.message.add_reaction("❌") # note that youll get X reactions even if other users work, might fix
            print(f"{memb} had no UserInfo table to give awards to")
            return

        awardinfo = crs.execute("SELECT * FROM AwardInfo WHERE NAME == (?)", (a,)) # award info
        l_award = list(awardinfo)
        user_awards = crs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (memb.id,)) # user awards list
        u_awards = list(user_awards)

        if l_award and u_awards:
            l_award = l_award[0] # access tuple
            u_awards = u_awards[0]
            print(f"{memb} is recieving: {l_award[3]}") # disp name
            datestring = f"{datetime.now().month}_{datetime.now().day}_{datetime.now().year}"
            if u_awards[0]: # if user has existing awards, add to string in db
                crs.execute("UPDATE UserInfo SET AWARDS = AWARDS || (?) WHERE ID == (?)", (f"{l_award[1]}/{datestring}/NF,", memb.id,))
            else: # if first user award
                print(f"{memb} had no existing awards")
                crs.execute("UPDATE UserInfo SET AWARDS = (?) WHERE ID == (?)", (f"{l_award[1]}/{datestring}/NF,", memb.id,))
            cn.commit()
            return True
            # await ctx.message.add_reaction("✅")
            # print(f"new userinfo for {member}: {list(curs.execute('SELECT * FROM UserInfo WHERE ID == (?)', (member.id,)))}")
        else:
            await ctx.send(f"{ctx.author.mention} This award doesn't exist!")
            print(f"Awards.giveaward, {ctx.author}; Attempted to give {memb} nonexistant award: {a}")
            return


    @commands.command(aliases=["gaward", "ga"])
    @commands.has_any_role("bareky", "♕") # replace w/ cog check?
    async def giveaward(self, ctx, award="NULL", *mentions):
        award = award.lower()
        users = []
        con = self.bot.database
        curs = self.bot.cursor
        res = None
        for m in mentions:
            member = extra.get_user(ctx, m)
            if member != None:
                users.append(member)

        for u in users:
            res = await Awards.ga_funct(ctx, con, curs, award, u)
            if res == True:
                print(f"caller: {ctx.author}, giveaward; {u} has successfully recieved {award}")
                await ctx.message.add_reaction("✅")
            else:
                print(f"caller: {ctx.author}, giveaward; {u} has not recieved {award}")
                await ctx.message.add_reaction("⚠️")


    async def ra_funct(ctx, cn, crs, a, memb):
        userinfo = list(crs.execute("SELECT * FROM UserInfo WHERE ID == (?)", (memb.id,)))
        if not userinfo:
            await ctx.message.add_reaction("❌")
            print(f"{ctx.author}, removeaward; {memb} had no UserInfo table to remove awards from")
            return

        user_awards = crs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (memb.id,))
        u_awards = list(user_awards)[0][0] # get string from cursor
        awardspl = u_awards.split(",")
        # print(f"before: {u_awards}")
        # loop through awards, find match to passed in award, remove that award from list
        for aw in awardspl:
            if aw.split("/")[0] == a: # split date
                awardspl.remove(aw)
        awardstr = ",".join(awardspl)
        crs.execute("UPDATE UserInfo SET AWARDS = (?) WHERE ID == (?)", (awardstr, memb.id,))
        cn.commit()
        await ctx.message.add_reaction("✅")
        # print(list(curs.execute("SELECT * FROM UserInfo WHERE ID == (?)", (member.id,))))

    @commands.command(aliases=['raward', "ra"])
    @commands.has_any_role("bareky", "♕")
    async def removeaward(self, ctx, award="NULL", *mentions):
        award = award.lower()
        users = []
        con = self.bot.database
        curs = self.bot.cursor
        for m in mentions:
            member = extra.get_user(ctx, m)
            if member != None:
                users.append(member)

        for u in users:
            await Awards.ra_funct(ctx, con, curs, award, u)

    @commands.command()
    @commands.has_any_role("bareky", "♕")
    async def oldcheck(self, ctx, award="NULL"):
        user = ctx.author
        if award == None:
            await ctx.send(f"{ctx.author.mention} Specify an award you own!")
            return
        award = award.lower()
        con = self.bot.database
        curs = self.bot.cursor
        award_embed = discord.Embed(description="NULL")

        awardlist = curs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (ctx.author.id,))
        u_awards = list(awardlist)[0][0]
        awardspl = u_awards.split(",") # seperate awards
        for a in awardspl:
            aspl = a.split("/") # seperate name and obtain date
            if aspl[0] == award:
                awardinfo = curs.execute("SELECT * FROM AwardInfo WHERE NAME == (?)", (aspl[0],)) # name in users list will be the same as in AwardInfo
                awardinfo = list(awardinfo)[0]
                award_embed.title = f"{awardinfo[4]} {awardinfo[3]}"
                award_embed.add_field(name="Obtained By", value=f"{ctx.author.name}", inline=True)
                datespl = aspl[1].split("_")
                award_embed.add_field(name="First Obtained", value=f"{datespl[0]}/{datespl[1]}/{datespl[2]}", inline=True)
                award_embed.description = awardinfo[2]
                award_embed.color = discord.Color.from_rgb(252,217,78) # could have specific colors for awards but for now it'll just be this
                break

        if award_embed.description != "NULL":
            await ctx.send(embed=award_embed)
        else:
            await ctx.send(f"{ctx.author.mention} Could not get award info, make sure you own the award!")

    @commands.command()
    async def awardinfo(self, ctx, *award):
        user = ctx.author
        if award == "NULL":
            await ctx.send(f"{ctx.author.mention} Specify an award you own!")
            return
        con = self.bot.database
        curs = self.bot.cursor
        award = " ".join(list(award)) # make *award into list, then join into lowered string
        award_fet = curs.execute("SELECT * FROM AwardInfo WHERE DISPNAME == (?)", (award,))
        award_fet = curs.fetchall()
        debug_name = None
        if award_fet:
            award_fet = award_fet[0]
            debug_name = award_fet[1]
        else:
            await ctx.send(f"{ctx.author.mention} Couldn't find award. This command is case sensitive!") # change to not be?
            return

        award_embed = discord.Embed(title=f"{award_fet[4]} {award_fet[3]}")
        # check if user owns awards for secrets
        u_awards = curs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (user.id,))
        datespl = None
        a_owned = False
        if u_awards:
            u_awards = curs.fetchall()[0][0] # access awards string
            awardspl = u_awards.split(",")
            for a in awardspl:
                aspl = a.split("/")
                if aspl[0] == debug_name:
                    a_owned = True
                    datespl = aspl[1].split("_")
                    break
        else:
            print(f"{ctx.author} called awardinfo with no awards")

        award_embed.color = discord.Color.from_rgb(252,217,78)
        if a_owned == False and award_fet[8] == True: # might have to be if award_fet == 1
            award_embed.description = "*???*"
        else:
            award_embed.description = f"{award_fet[2]}"
        if a_owned == True:
            award_embed.add_field(name="Obtained By", value=f"{ctx.author.name}", inline=True)
            award_embed.add_field(name="First Obtained", value=f"{datespl[0]}/{datespl[1]}/{datespl[2]}", inline=True)

        await ctx.send(embed=award_embed)


    @commands.command()
    async def checkawards(self, ctx, mention="NULL", page: int=0):
        member = extra.get_user(ctx, mention)
        if member == None: return
        con = self.bot.database
        curs = self.bot.cursor

        i = 0
        pagesize = 5
        awards = list(curs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (member.id,)))
        if page != 0:
            i = pagesize-(page-1)
        try:
            awards = awards[0][0]
        except IndexError as ex:
            await ctx.send(f"{member.mention} has no awards to check")
            return

        # included because sommetimes would get past try/except
        if awards == None:
            await ctx.send(f"{member.mention} has no awards to check")
            return
        awardspl = awards.split(",")
        awardlist = []
        check_embed = discord.Embed(
            title=f"{member.name}'s Awards",
            color=discord.Color.from_rgb(252,217,78)
        )
        check_embed.set_thumbnail(url=member.avatar)
        awardtext = ""
        c = 0

        for a in awardspl:
            awardname = a.split("/")[0]
            award = curs.execute("SELECT * FROM AwardInfo WHERE NAME == (?)", (awardname,))
            award_fet = award.fetchall() # accessing tuple w/ list way doesnt work here, works similar though
            if award_fet:
                award_fet = award_fet[0]
                if c == 0:
                    awardtext = f"{award_fet[4]} {award_fet[3]}"
                else:
                    awardtext += f", {award_fet[4]} {award_fet[3]}"
            else:
                # should happen when a user has a corrupted award
                print(f"caller: {ctx.author}, checkawards; Could not find {awardname} award in {member.name} inven")
            c += 1
        check_embed.title += f" ({c-1})"
        check_embed.description = awardtext
        await ctx.send(embed=check_embed)

    @commands.command()
    async def awardlist(self, ctx):
        con = self.bot.database
        curs = self.bot.cursor
        award_embed = discord.Embed(
            title=f"Cruisebot Awards",
            color=discord.Color.from_rgb(252,217,78)
        )

        awards = curs.execute("SELECT * FROM AwardInfo;")
        awards = awards.fetchall()
        c = 0
        for r in range(len(awards)):
            if awards[r][7] == False:
                if c == 0:
                    award_embed.description = f"{awards[r][4]} {awards[r][3]}"
                else:
                    award_embed.description += f", {awards[r][4]} {awards[r][3]}"
                c += 1

        await ctx.send(embed=award_embed)

    @commands.command(aliases=['feature'])
    async def featureaward(self, ctx, *award):
        user = ctx.author
        con = self.bot.database
        curs = self.bot.cursor
        award = list(award)
        awardstr = " ".join(award)

        # needed for display name usage
        a_name = Awards.match_award(con, curs, awardstr, user)
        if a_name != None:
            u_awards = curs.execute("SELECT AWARDS FROM UserInfo WHERE ID == (?)", (user.id,))
            u_awards = list(u_awards)[0][0]
            u_awards_spl = u_awards.split(",")

            for a in u_awards_spl:
                aspl = a.split("/")
                try:
                    aspl[2]
                except IndexError as ex:
                    # print(f"caller: {ctx.author}; Award {aspl[0]} had no feature attribute")
                    continue
                if a_name == aspl[0]:
                    u_awards_spl.remove(a) # remove old award

                    if aspl[2] == "NF" and len(u_awards_spl) > 1:
                        aspl[2] = "F"
                        new_award = f"{aspl[0]}/{aspl[1]}/{aspl[2]}"
                        u_awards_spl.append(new_award)
                        text = f"{ctx.author.mention} Award {aspl[0].title()} is now featured on your profile."
                    elif aspl[2] == "F" and len(u_awards_spl) > 1:
                        aspl[2] = "NF"
                        new_award = f"{aspl[0]}/{aspl[1]}/{aspl[2]}"
                        u_awards_spl.append(new_award)
                        text = f"{ctx.author.mention} Award {aspl[0].title()} is no longer featured on your profile."
                    # replace old award w/ new
                    print(text)
                    u_awards_str = ",".join(u_awards_spl)
                    u_awards_str += "," # add comma to end for sep
                    # print(u_awards_str)
                    curs.execute("UPDATE UserInfo SET AWARDS = (?) WHERE ID == (?)", (u_awards_str, user.id,))
                    con.commit()
                    await ctx.send(text)
                    return
            await ctx.send(f"{ctx.author.mention} Unable to feature award.")
        else:
            await ctx.send(f"{user.mention} You don't own that award!")
            return


async def setup(bot):
    await bot.add_cog(Awards(bot))
