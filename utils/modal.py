import discord,json,logging
import config
from utils.utils import id3toid64

logger = logging.getLogger("csbot")

users_cache = {}
with open("data/users.json", "r") as f:
        users_cache = json.load(f)

class registerModal(discord.ui.Modal, title="CS2 Rating Leaderboard Registration"):
    friendcode = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Your Steam Friendcode:",
        required=True,
        max_length=20,
        placeholder="Example: '232012894'"
        
    )
    async def on_submit(self, interaction: discord.Interaction):
        logger.info("Submitting modal")

        name = str(self.user.display_name) if str(self.user.display_name) else str(self.user.name)

        log_channel = interaction.guild.get_channel(config.log_channel_id)
        log = f"{name} just submitted the form (Input: \"{str(self.friendcode)}\")"
        await log_channel.send(log)

        if str(self.user.global_name) in users_cache.keys():
            logger.info("Already registered")
            log = f"{name} got response \"You are already registered.\""
            await log_channel.send(log)
            await interaction.response.send_message("You are already registered.", ephemeral=True)
            return
        if not str(self.friendcode).isnumeric():
            logger.info("Non numeric friendcode")
            log = f"{name} got response \"Please input an actual steam friend code.\""
            await log_channel.send(log)
            await interaction.response.send_message("Please input an actual steam friend code.", ephemeral=True)
            return
        
        try:
            id64 = str(id3toid64(str(self.friendcode)))
        except Exception:
            log = f"{name} got response \"Please input an actual steam friend code.\""
            await log_channel.send(log)
            await interaction.response.send_message("Please input an actual steam friend code.", ephemeral=True)

        if not id64.isnumeric():
            logger.info("Non numeric friendcode")
            log = f"{name} got response \"Please input an actual steam friend code.\""
            await log_channel.send(log)
            await interaction.response.send_message("Please input an actual steam friend code.", ephemeral=True)
            return

        users_cache[str(name)] = {"name":str(name),"discord_id":str(self.user.id),"friendcode":str(self.friendcode), "id64":str(id64)}

        log = f"{name} just registered! (Discord ID: {users_cache[name]['id64']}, Friendcode: {users_cache[name]['friendcode']} interpreted as ID64: {users_cache[name]['id64']})"
        logger.info(log)
        await log_channel.send(log)

        with open("data/users.json", "w") as f:
            json.dump(users_cache, f)

        await interaction.response.send_message("Successfully registered!", ephemeral=True)
    
    async def on_error(self, interaction: discord.Interaction, error):
        return