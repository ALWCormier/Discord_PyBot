from discord.ext import commands
import discord
import bs4 as bs
import urllib.request
import json
import numpy as np
import cv2
import os
from discord.ext.commands import MissingRequiredArgument

TOKEN = "your_token_here"

bot = commands.Bot(command_prefix="'")
client = discord.Client()

def url_opener(url):
    site = urllib.request.urlopen(url).read()
    try:
        soup = bs.BeautifulSoup(site, 'html.parser')
        return soup
    except:
        print("bad soup")


#gets pokedex number for a given pokemon from an external json
def nat_dex_number(name):
    with open("pokedata.json", 'r') as database:
        dex_data = json.load(database)
        dex_number = ""
        for entry in dex_data:
            if entry.lower() == str(name.lower()):
                dex_number = dex_data[entry]
    return dex_number

#check if pokemon is in the gen8 dex
def gen_8_dex(poke_name):
    exists = False

    with open("galan_dex_names.json", 'r') as gen8_dex:
        dex = json.load(gen8_dex)
        for name in dex:
            if name.lower() == poke_name:
                exists = True
                break

    return exists


#next evolution name from dex number and json file
def next_evolution_name(dex_number, poke_name, family):
    i=0
    nex_dex = ' '
    mega=False
    for item in family:
        if item[-9:-6] == dex_number or item[-len(poke_name):] == poke_name:
            try:
                next_ev = family[i+1]
                if next_ev[-5:] == "#mega":
                    mega = True
                    nex_dex = dex_number
                else:
                    if item[-len(poke_name):] == poke_name:
                        temp = (family[i+1].split("/"))
                        nex_dex = temp[-1]
                    else:
                        nex_dex = family[i+1][-9:-6]
            except:
                return " "
        i += 1
    if nex_dex == ' ':
        return " "
    if len(nex_dex) == 3:
        with open("pokedata.json", 'r') as database:
            dex_data = json.load(database)
            for key in dex_data:
                if dex_data[key] == nex_dex:
                    if mega:
                        return "Mega "+key.title()
                    else:
                        return key.title()
    else:
        return nex_dex.title()


def concat_img(type_list, axis):
    i = 1
    img = cv2.imread("type_images/" + type_list[0] + ".png")
    while i < len(type_list):
        temp = cv2.imread("type_images/" + type_list[i] + ".png")
        img = np.concatenate((img, temp), axis=axis)
        i += 1
    cv2.imwrite('out.png', img)
    file = discord.File('out.png')
    return file


def delete_file(file):
    try:
        os.remove(file)
    except OSError as e:
        print(e)


def serebii_scrape(dex_number, poke_name, gen):
    #dictionary with standard gen numbers to serebii gen prefixes
    gen_acros = {"1":"/", "2":"-gs/", "3":"-rs/", "4":"-dp/", "5":"-bw/", "6":"-xy/", "7":"-sm/", "8":"-swsh/"}
    link_prefix = "https://www.serebii.net"

    #initialize some return variables
    evo_images = []
    abilities = []
    evo_method = 0
    real = False

    # if gen 8 compare poke name w/ new nat dex
    if int(gen) == 8:
        url = link_prefix + "/pokedex" + gen_acros[gen] + poke_name + "/"
        real = True
        # use beautiful soup to get a html parsed page
        soup = url_opener(url)
    else:
        url = "https://www.serebii.net/pokedex" + gen_acros[gen] + dex_number + ".shtml"
        # use beautiful soup to get a html parsed page
        soup = url_opener(url)


    # open url as soup, get regular poke sprite
    # data getting process differs depending on game gen

    if (int(gen) > 5) or real:
        #get the image link for the sprite embed
        sprite_link = soup.find("img", {"alt": "Normal Sprite"})
        sprite_link = str(sprite_link.get('src'))
        sprite_link = link_prefix+sprite_link

        #get type images
        types = soup.find_all("img", {"class": "typeimg"})
        i = 0
        for item in types:
            #manipulate image link to type
            types[i] = str(item.get('src'))
            types[i] = types[i].split('/')
            types[i] = types[i][-1]
            types[i] = types[i][:-4]
            i += 1
        type_file = concat_img(types, 0)

        #get all the images in the evolution chain section
        chain = soup.find_all("table", {"class": "evochain"})
        temp_string = ""
        family = []
        for image in chain:
            temp_string += str(image)
        chain = temp_string.split('"')
        for item in chain:
            if item[:8] == "/pokedex":
                if item[8+len(gen_acros[gen]):15+len(gen_acros[gen])] == "evoicon":
                    evo_images.append(link_prefix + item)
                else:
                    evo_images.append(link_prefix+item)
                    ####    for next evolution
                    print(item)
                    family.append(item)

            elif item[:7] == "evoicon":
                evo_images.append("https://www.serebii.net/pokedex"+gen_acros[gen]+item)

        #if the url has the pokedex number of the current pokemon, get the level it evolves
        i = 0
        for item in evo_images:
            if gen == "8":
                if item[-len(poke_name):]:
                    try:
                        evo_method = evo_images[i+1]
                        break
                    except:
                        evo_method = 0

            else:
                if item[-9:-6] == str(dex_number):
                    try:
                        evo_method = evo_images[i+1]
                        break
                    except:
                        evo_method = 0

            i += 1

        #get ability text
        for item in soup.find_all('b'):
            if item.parent.name == 'a':
                if str(item.parent)[10:17] == "ability":
                    abilities.append(item.get_text())
                    abilities.append(item.parent.parent.get_text())
        abilities = str(abilities[-1])

        n_evo_name = next_evolution_name(dex_number, poke_name, family)

        return sprite_link, type_file, evo_method, url, abilities, n_evo_name

    else:
        link_number = 0
        for item in soup.find_all('img'):
            if item.parent.name == 'td':
                link_number += 1
                if link_number == 2:
                    sprite_link = str(item.get('src'))
                    sprite_link = link_prefix + sprite_link
                    return sprite_link, [], 0, url, ''


#for dexes older than 5(?) search for paragraph with "general" tag, from that TR with "evolution chain" text in a subset <b> tag
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        await ctx.send("Please pass in all required arguments.")


# set "game" visible on client
@bot.event
async def on_ready():
    print("Bot Online")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('coming soon to theaters'))


@bot.command()
async def poke(ctx, *, args):
    arg_data = (args.lower()).split(" ")
    print(arg_data)

    #checks for pokemon with two word names, checks for specified gen, defaults to gen7
    if arg_data[0] == "mr." or arg_data[0] == "type:" or arg_data[0] == "mime":
        poke_name = arg_data[0]+" "+arg_data[1]
        try:
            gen = arg_data[2]
        except:
            gen = "8"
    else:
        poke_name = arg_data[0]
        try:
            gen = arg_data[1]
            print(gen)
        except:
            gen = "8"

    dex_number = nat_dex_number(poke_name)

    #if
    if (dex_number != "") or gen_8_dex(poke_name):
        #scrapes serebii page, returns a list including: sprite_link, type_file, evo_method, url, abilities, n_evo_name
        poke_data = serebii_scrape(dex_number, poke_name, gen)

        #allows type images to be used in embed through discord attachment link
        await ctx.send(file=poke_data[1])
        message = await ctx.channel.history(limit=1).flatten()
        message = (str(message[0].attachments).split("'"))[3]

        #creates embed and fields
        embed = discord.Embed(title=poke_name.title(), color=0x00ffff).set_thumbnail(url=poke_data[2]).set_author(name='Type', icon_url=message)
        if poke_data[0] != " ":
            embed.set_image(url=poke_data[0])
        embed.add_field(name="Abilties", value=poke_data[4])
        embed.add_field(name="Link: ", value=poke_data[3])
        embed.add_field(name="Evolution Method:", value ="Next Evolution: "+poke_data[5])
        await ctx.send(embed=embed)
        embed2 = discord.Embed(title="Types:", color=0x00ffff)
        await ctx.send(embed=embed2, attachments=poke_data[1])
    else:
        await ctx.send("No matching pokemon")


@bot.command()
async def t(ctx, *, args):
    arg_data = (args.lower()).split(" ")
    element = arg_data[0]
    super_effective = []
    nv_effective = []
    no_effect = []
    real = True

    #checks for an attack/defense argument, defaults to defense
    try:
        mode = arg_data[1]
    except:
        mode = "defense"

    #opens the appropriate table and sets output text
    if mode == "defense":
        with open("defense_effectiveness.json") as table:
            effectiveness = json.load(table)
        sf_display_text = " is weak to:"
        nv_display_text = " is resistant to:"
        nf_display_text = " is not effected by:"

    else:
        with open("attack_effectiveness.json") as table:
            effectiveness = json.load(table)
        sf_display_text = " is super effective against:"
        nv_display_text = " is not very effective against:"
        nf_display_text = " has no effect on:"

    #loops through types and sorts by super effective(2), not very effective (1), and no effect (0)
    for key in effectiveness:
        if key == element:
            i = 0
            for item in effectiveness[key]:
                if effectiveness[key][i][1] == 2:
                    super_effective.append(effectiveness[key][i][0])
                elif effectiveness[key][i][1] == 1:
                    nv_effective.append(effectiveness[key][i][0])
                else:
                    no_effect.append(effectiveness[key][i][0])
                i += 1
            break

    #gets type icons and adds them together to display
    if len(super_effective) != 0:
        #creates temporary file for display
        file = concat_img(super_effective, 1)

        embed = discord.Embed(title=element.title() + sf_display_text, color=0x00ffff)
        await ctx.send(embed=embed)
        await ctx.send(file=file)

        #deletes the temporary file created after it has been sent
        delete_file("out.png")
    else:
        real = False

    if len(nv_effective) != 0:
        #creates temporary file for display
        file = concat_img(nv_effective, 1)

        embed = discord.Embed(title=element.title() + nv_display_text, color=0x00ffff)
        await ctx.send(embed=embed)
        await ctx.send(file=file)

        # deletes file
        delete_file("out.png")

    if len(no_effect) != 0:
        # creates temporary file for display
        file = concat_img(no_effect, 1)

        embed = discord.Embed(title=element.title() + nf_display_text, color=0x00ffff)
        await ctx.send(embed=embed)
        await ctx.send(file=file)

        # deletes file
        delete_file("out.png")

    if not real:
        await ctx.send("Not a pokemon type")

bot.run(TOKEN)