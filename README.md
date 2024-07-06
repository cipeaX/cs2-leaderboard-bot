# CS2 Leaderboard Bot
Discord Bot for displaying a self-updating Leaderboard for CS2 Premier Ratings in small Communities and managing rating-based Roles for Members.

# Setup:
- Clone repository
- `pip install -r requirements.txt`
- Upload Emojis to your Discord Server
- Create Roles for every CS2 Rating (see config.py) as well as 2 new Channels (Leaderboard & Log-Channel)
- Fill out config.py (Bot Token, GuildID, ChannelIDs, EmojiIDs)
- `python bot.py` to run the Bot

Members will have to register themselves with /register and their Steam Friendcode to appear on the Leaderboard and get the Roles.