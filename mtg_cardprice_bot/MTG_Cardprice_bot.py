from discord.ext import commands
import discord
import bs4 as bs
import urllib.request
import json
from discord.ext.commands import MissingRequiredArgument

TOKEN = "your_token_here"

bot = commands.Bot(command_prefix=";")
client = discord.Client()


# makes BS object given url
def url_opener(url):
    site = urllib.request.urlopen(url).read()
    try:
        soup = bs.BeautifulSoup(site, 'html.parser')
    except:
        print("bad soup")
    return soup


def name_set_format(array):
    for item in array:
        del item[0:2]
        i = 0
        for string in item:
            item[i] = string.replace("+", " ")
            i += 1


def mtggoldfish_scrape(card_name):
    address1 = "https://www.mtggoldfish.com/q?utf8=?&query_string="
    address2 = "&set_id=&commit=Search"
    name = card_name
    card_name = card_name.replace(" ", "+")
    url_prime = address1 + card_name + address2
    soup = url_opener(url_prime)

    b_links = []
    b_images = []

    f_links = []
    f_images = []
    link_prefix = "https://www.mtggoldfish.com"
    name_set = []

    # get current page
    webp_check = soup.find_all('meta', {"property": "og:url"})
    webp_check = str(webp_check)
    current_page = webp_check[16:-22]
    webp_check = webp_check[44:49]

    # checks for single card redirect
    if webp_check == 'price':

        # gets image from that page
        image = (soup.find_all('img')[6]['src'])
        f_images.append(image)
        name_set.append(current_page[27:].split('/'))
        f_links.append(current_page)

        # get foil info
        try:
            name_set_format(name_set)
            setid = len(name_set[0][0])

            # add and altered link to foil version to links to be passed
            f_links.append(current_page[:34+setid]+':Foil'+current_page[34+setid:])
            name_set.append([name_set[0][0]+':Foil', name_set[0][1]])
        except:
            print("nonfoil")

    else:

        # make a list of all initial URLS and Images
        for url in soup.find_all('a', href=True):
            b_links.append((url.get('href')))
            b_images.append((url.get('data-full-image')))
        # get a list of set images for card
        for item in b_images:
            if item is not None:
                f_images.append(item)

        # get a list of price links
        for item in b_links:
            if item[0:7] == "/price/":
                f_links.append(link_prefix + item)
                name_set.append(item.split('/'))

        name_set_format(name_set)
    # control switch for real cards
    if len(f_links) == 0:
        not_card = "True"
    else:
        not_card = "False"

    return name_set, f_links, f_images, not_card, name


def price_getter(soup):
    spans = soup.find_all("div", {"class": "btn-shop-label"})
    i = 0
    for item in spans:
        if item.text[2:-1] == "TCGplayer Market Price":
            price = str(item.find_next_siblings())
            break
        else:
            price = "--"
    return price[33:-42]

# @bot.event
# async def on_message(ctx):
#     print(ctx.author.id)
#     if str(ctx.author.id) == 240537940378386442:
#         return

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        await ctx.send("Please pass in all required arguments.")

# set "game" visible on client
@bot.event
async def on_ready():
    print("Bot Online")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('Try ;commands'))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount=10):
    await ctx.channel.purge(limit=amount)

@bot.command()
async def card(ctx, *, args):
    card_name = args
    data = mtggoldfish_scrape(card_name)
    name_set = data[0]
    f_links = data[1]
    f_images = data[2]
    user_input = data[4].replace(",","")
    user_input = user_input.replace("'", "")
    a = 0 #adjust for undesirable results
    i = 0 #an index ofc

    #checks if real card
    if data[3] == "False":

        # circumvents MTGGOLDFISH's obnoxious alphabetized results
        while (name_set[i][1][0:len(user_input)]).lower() != user_input.lower():
            a += 1
            i += 1

        # checks for dummy sets and adjust past them

        #get price page from url
        soup = url_opener(f_links[0+a])

        #get scrape tcg market price from page
        f_price = price_getter(soup)

        f_images.append(soup.find_all("img", {"class": "price-card-image-image"}))
        image = str(f_images[0+a])

    #start output with embed
        embed = discord.Embed(title=name_set[0+a][1], color=0x00ffff)
        embed.set_image(url=image)
        embed.add_field(name=name_set[0+a][0], value="TCG Market Price: " + f_price, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Not a card {ctx.author.mention}")



@bot.command()
async def price(ctx, *, args):
    card_name = args
    data = mtggoldfish_scrape(card_name)
    name_set = data[0]
    f_links = data[1]
    a = 0
    i = 0
    count = 0

    if data[3] == "False":

        # makes sure title is not avatar
        # print(name_set[i][0][0:8])
        while name_set[i][0][0:8] == "Vanguard" or name_set[i][0][0:8] == "Duels of" or name_set[i][0][0:8] == "Promotio":
            a += 1
            i += 1

        embed = discord.Embed(title=name_set[0+a][1], color=0x00ffff)
        # print(name_set[0+a][1])

        i = 0
        for item in f_links:
            #make sure there are only 10 results for time's sake
            if count > 9:
                break

            try:
                soup2 = url_opener(item)
                f_price = price_getter(soup2)
            except:
                print("something broke")

            if f_price[-3:] != "tix" and f_price != "":
                embed.add_field(name=name_set[i][1] + " | " + name_set[i][0], value="Price: " + f_price, inline=False)
                count += 1

            i+= 1
        print("here")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Not a card {ctx.author.mention}")


# adds a new deck to a locally stored file for deck storage
@bot.command()
async def add(ctx, *, args):
    stff = args.split(' ')
    name = stff[0]
    name = (name.replace("_", " "))
    name = name.title()
    link = stff[1]
    owner = str(ctx.author.id)

    # opens json dicts
    with open("decklist_links.json") as database:
        try:
            decks = json.load(database)
        except:
            decks = {"dummy": [["dummy", "dummy"], ["dummy", "dummy"]]}

    new = True

    for user in decks.keys():
        #if user already has decks, add another
        if str(owner) == user:
            new = False

    # add a new user with first deck
    if not new:
        decks[str(owner)].append([name, str(link)])
    else:
        decks[str(owner)] = [[name, str(link)]]

    with open("decklist_links.json", 'w') as database:
        json.dump(decks, database)


# deletes a deck given 1-indexed index or name
@bot.command()
async def cut(ctx, *, args):
    user = str(ctx.author.id)
    decklist_i = int(args)
    q =False

    with open("decklist_links.json") as database:
        decks = json.load(database)
        for tag in decks.keys():
            #find their decks
            if str(tag) == user:
                for item in range(len(decks[tag])):
                    if str(item) == str(decklist_i -1):
                        del decks[tag][int(item)]
                        with open("decklist_links.json", 'w') as database:
                            json.dump(decks, database)
                        q = True
                        break
    if not q:
        await ctx.send("You don't have enough decks for that")


# displays deck for mentioned user
@bot.command()
async def decks(ctx, mention : discord.Member):

    mention = str(mention.id)
    all_decks = {}
    has_decks = False
    embed = discord.Embed(title="Decks:", color=0x00ffff)

    with open("decklist_links.json") as database:
        all_decks = json.load(database)

        for item in all_decks.keys():
            if item == mention:
                has_decks = True
                break

    if has_decks:
        for item in range(len(all_decks[mention])):
            embed.add_field(name=all_decks[mention][item][0]+":", value=all_decks[mention][item][1], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Mentioned User has no decks uploaded")


# shows commands
@bot.command()
async def commands(ctx):
    embed = discord.Embed(title="Commands:", color=0x00ffff)
    embed.add_field(name=";card cardname", value="Display card image and price", inline=False)
    embed.add_field(name=";price cardname", value="Lists prices for card", inline=False)
    embed.add_field(name=";add deck_title link", value="Adds decklist to your file (use '_' instead of spaces or your entry will be ruined)", inline=False)
    embed.add_field(name=";cut #", value="Removes deck number # from your list", inline=False)
    embed.add_field(name=";decks @mention", value="Lists mentioned user's decks on file", inline=False)

    await ctx.send(embed=embed)

bot.run(TOKEN)