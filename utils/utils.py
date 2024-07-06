import json,datetime,httpx,asyncio,logging
import config

logger = logging.getLogger("csbot")

async def get_ratings_from_id64s_async(list):

    async with httpx.AsyncClient() as client:
        tasks = (client.get(url=f"https://api.leetify.com/api/profile/{id64}", timeout=30) for id64 in list)
        reqs = await asyncio.gather(*tasks, return_exceptions=True)

    errors = [(req.status_code,req.url) for req in reqs if req.status_code != 200]
    if errors:
          raise Exception(f"Leetify Status: {errors}")

    ress = [json.loads(req.text) for req in reqs]


    for i, id64 in enumerate(list):

        res = ress[i]
        done = False
        for game in [g for g in res["games"] if g["isCs2"]][:25]:

            #check if premier match
            if(game["skillLevel"]):
                if(game["skillLevel"] < 1000): # skillLevel < 1000 -> normal matchmaking
                    continue

            #check if after season reset
            matchdate = datetime.datetime.fromisoformat(str(game["gameFinishedAt"][:-1])).astimezone(datetime.timezone.utc)
            if matchdate < datetime.datetime.fromtimestamp(config.last_season_reset_date).astimezone(datetime.timezone.utc):
                logger.debug(f"No match after reset for {id64}")
                list[i], done = "--,---", True
                break

            #check if within last 2 weeks
            if (datetime.datetime.now(tz=datetime.timezone.utc) - matchdate).days > 14:
                logger.debug(f"Rank decayed for {id64}")
                list[i], done = "--,---", True
                break

            rating = str(game["skillLevel"])
            if rating == "0" or rating == "None":
                list[i], done = "--,---", True
                break
            rating = rating[:-3] + "," + rating[-3:]
            if len(rating) == 5:
                rating = "0" + rating
            list[i], done = rating, True
            break

        if not done:
            logger.debug(f"Couldnt find CS2 match for {id64}")
            list[i] = "--,---"
    
    return list


def id3toid64(id3):
    id3 = int(id3)
    if id3 % 2 == 0:
        y = 0
        z = id3/2
    else:
        y = 1
        z = (id3 - 1) / 2
    
    return f"7656119{int(z * 2) + int(7960265728 + y)}"


if __name__ == "__main__":
    pass



    

