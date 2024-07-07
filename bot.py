import discord,time,asyncio,json,copy,logging
from discord.ext import commands, tasks
from utils.utils import get_ratings_from_id64s_async
import utils.modal
import config

### GLOBALS
cs2guild = None
log_channel = None

role_gold = None
role_red = None
role_pink = None
role_purple = None
role_blue = None
role_lightblue = None
role_white = None
role_unrated = None

### LOGGING
logger = logging.getLogger("csbot")
logger.setLevel(level=logging.DEBUG)
loghandler_stdout = logging.StreamHandler()
logformatter = logging.Formatter('{asctime} {levelname:<8} {name} {message}', '%Y-%m-%d %H:%M:%S', style='{')
loghandler_stdout.setFormatter(logformatter)
logger.addHandler(loghandler_stdout)

### LOAD USERS
users_cache = {}
with open("data/users.json", "r") as f:
        users_cache = json.load(f)

def ratings_helper(id64s):
    ratings = asyncio.run(get_ratings_from_id64s_async(id64s))
    return ratings

activity = discord.Activity(type=discord.ActivityType.watching, name="/register")
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), activity=activity, status=discord.Status.online)

@bot.event
async def on_ready():
    logger.info("Bot started")
    try:
        synced = await bot.tree.sync()
        logger.debug("Synced commands")
    except Exception as e:
        logger.debug(e)

    global cs2guild
    global log_channel
 
    global role_gold
    global role_red
    global role_pink
    global role_purple
    global role_blue
    global role_lightblue
    global role_white
    global role_unrated

    cs2guild = bot.get_guild(config.guild_id)
    log_channel = bot.get_channel(config.log_channel_id)

    role_gold = discord.utils.get(cs2guild.roles, name = config.gold_role_name)
    role_red = discord.utils.get(cs2guild.roles, name = config.red_role_name)
    role_pink = discord.utils.get(cs2guild.roles, name = config.pink_role_name)
    role_purple = discord.utils.get(cs2guild.roles, name = config.purple_role_name)
    role_blue = discord.utils.get(cs2guild.roles, name = config.blue_role_name)
    role_lightblue = discord.utils.get(cs2guild.roles, name = config.lightblue_role_name)
    role_white = discord.utils.get(cs2guild.roles, name = config.white_role_name)
    role_unrated = discord.utils.get(cs2guild.roles, name = config.unrated_role_name)
    
    updateLoop.start()
    

@bot.tree.command(name="register", description="Register to the CS Rating Bot")
async def register(interaction: discord.Interaction):
    logger.info("Opening modal")
    reg_modal = utils.modal.registerModal()
    reg_modal.user = interaction.user
    log_channel = interaction.guild.get_channel(config.log_channel_id)
    log = f"{interaction.user.global_name} just used /register and opened the form"
    await log_channel.send(log)
    await interaction.response.send_modal(reg_modal)


@tasks.loop(seconds = 300) # repeat every 5 minutes
async def updateLoop():
    logger.debug("Updating from loop")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/register"))

    users_cache = {}
    with open("data/users.json", "r") as f:
        users_cache = json.load(f)
        
    channel = bot.get_channel(config.leaderboard_channel_id)
    
    embed = discord.Embed(title="CS2 Leaderboard")

    users_plus = copy.deepcopy(users_cache)
    for user in users_plus.keys():
        users_plus[user]["member"] = await cs2guild.fetch_member(users_plus[user]["id"])

    id64s = [users_plus[key]["id64"] for key in users_plus.keys()]

    try: 
        loop = asyncio.get_running_loop()
        ratings = await loop.run_in_executor(None, ratings_helper, id64s) 
    except Exception as e:
        await log_channel.send("Error in updateLoop:" + str(e))
        logger.error("Error in updateLoop")
        return
    
    
    for i, key in enumerate(users_plus):
        users_plus[key]["rating"] = ratings[i]

    users_plus_sorted = sorted(users_plus.values(), key=lambda x: x["rating"], reverse=True)

    emojis = [config.emoji_30k35k,config.emoji_25k30k,config.emoji_20k25k,config.emoji_15k20k,config.emoji_10k15k,config.emoji_5k10k,config.emoji_0k5k,config.emoji_unrated][::-1]


    desc_string = "Go `/register` yourself to appear here!\n\n"
    
    for user_entry in users_plus_sorted:
        rating = user_entry['rating']
        emoji = ""
        if rating == "--,---":
            emoji = emojis[0]
        else:
            rating_int = int(rating.replace(",",""))
            rating_index = int(rating_int/5000)+1
            emoji = emojis[rating_index]
        if rating[0] == "0":
            rating[0] = " "

        desc_string += f"{emoji}`{user_entry['name']:25}{rating} `  **[👤+](https://steamcommunity.com/profiles/{user_entry['id64']})**\n\n"
        
    embed.description = desc_string
    embed.add_field(name="", value="Last updated <t:" + str(int(time.time())) + ":R>", inline=False)

    if len(embed) > 4000:
        msg = "Embed got too long (Discord limits embeds to 4096 characters). To handle more users u gotta implement a way to split up the leaderboard into multiple messages. :)"
        logger.error(msg)
        await log_channel.send(msg)

    try:
        leaderboard_message = await channel.fetch_message(channel.last_message_id)
        await leaderboard_message.edit(embed=embed)
        logger.debug("Edited message")
    except Exception as e:
        async for msg in channel.history(limit=5):
            await msg.delete()
        await channel.send(embed=embed)
        logger.info("Created new message")

    await checkRoles(users_plus)
    return

async def checkRoles(users_plus):

    roles = [role_gold,role_red,role_pink,role_purple,role_blue,role_lightblue,role_white,role_unrated][::-1]
    
    for user in users_plus.values():
        reg_user = user["member"]
        rating = user["rating"]
        if rating == "--,---" and role_unrated not in reg_user.roles:
            await reg_user.remove_roles(*roles)
            await reg_user.add_roles(role_unrated)
            log = user["name"] + " just got the unranked role"
            logger.info(log)
            await log_channel.send(log)
            continue
        if rating == "--,---":
            continue
        rating_int = int(rating.replace(",",""))

        rating_index = int(rating_int/5000)+1
        if roles[rating_index] not in reg_user.roles:
            await reg_user.remove_roles(*roles)
            await reg_user.add_roles(roles[rating_index])
            log = f"{user['name']} just got the {roles[rating_index].name} role"
            logger.info(log)
            await log_channel.send(log)
            continue
    
    logger.debug("Checked roles")
    return

bot.run(token=config.token, log_handler=loghandler_stdout)
