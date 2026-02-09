import asyncio
from time import time

import discord
from loguru import logger

import RobloxPy
from config.colors import presenceTypeCode
from config.constants import GAME_ID

gameid_list = {}


async def manage_data_create_embed(
    presence: RobloxPy.Presence.Presences.UserPresence, bot, embeds, ALT_STATUS_CHANNEL
):
    if presence.userId not in gameid_list:
        gameid_list[presence.userId] = [
            ["nil", presence.jobId or "nil"],
            ["nil", f"<t:{round(time())}:R>"],
            presence.lobbyStatus,
            presence.lastlocation,
            presence.userPresenceType,
            ["nil", f"<t:{round(time())}:R>"],  # not safe time
        ]

    user_game_info = gameid_list[presence.userId]
    current_gameid = user_game_info[0][1]
    is_different_game = presence.jobId and current_gameid != presence.jobId
    is_offline = presence.userPresenceType == 0 and current_gameid
    message_sent = False

    if is_different_game or is_offline:
        if bot.tracking.get(presence.userId):
            try:
                result_time = round(time()) - int(user_game_info[1][1][3:-3])
                time_in_game = (
                    f"{result_time} Seconds"
                    if result_time < 60
                    else f"{result_time // 60}:{result_time % 60:02d} Minutes"
                )

                embed = discord.Embed(
                    title="Time in game: " + time_in_game, color=46847
                )

                embed.add_field(
                    name="From:",
                    value=f"Game: **{user_game_info[3]}**\nGameId: **{user_game_info[0][1]}**\nLobby: **{user_game_info[2]}**",
                    inline=True,
                )
                embed.add_field(
                    name="To:",
                    value=f"Game: **{presence.lastlocation}**\nGameId: **{presence.jobId}**\nLobby: **{presence.lobbyStatus}**",
                    inline=True,
                )

                await bot.tracking[presence.userId][0].send(
                    content=f"<t:{round(time())}:R>{"".join(bot.tracking[presence.userId][1])}",
                    embed=embed,
                )

            except Exception as e:
                logger.exception(e)

        user_game_info[2] = presence.lobbyStatus
        user_game_info[3] = presence.lastlocation
        user_game_info[1][0] = user_game_info[1][1]
        user_game_info[0][0] = current_gameid
        user_game_info[1][1] = f"<t:{round(time())}:R>"
        user_game_info[0][1] = presence.jobId

    if user_game_info[4] != presence.userPresenceType:
        user_game_info[5][0] = user_game_info[1][1]
        user_game_info[5][1] = f"<t:{round(time())}:R>"

    last_gameid = user_game_info[0][0]
    time_in_gameid = user_game_info[1][1]

    presence_type_code = presenceTypeCode[
        (
            presence.userPresenceType
            if presence.lobbyStatus == "True" or is_offline != False
            else "match"
        )
    ]

    color = presence_type_code[0]
    type = presence_type_code[1]

    title = f"{presence.username} {type}"
    description = f"Game: **{presence.lastlocation}**" + (
        f"\nLobby: **{presence.lobbyStatus}**\nGameId: **{presence.jobId}**\nLastGameId: **{last_gameid}**\nTime in gameId: **{time_in_gameid}**"
    )
    embed = discord.Embed(
        color=color,
        title=title,
        description=(
            description
            if presence.userPresenceType == 2 and presence.gameId != None
            else f"Time in game: **{user_game_info[5][1]}**"
        ),
    )

    if presence.groupName != "None":
        embed.set_footer(text=f"Group: {presence.groupName}")

    if presence.isAlt and (
        presence.userPresenceType == 2
        and not bot.MuteAll
        and (presence.gameId == None or presence.gameId == GAME_ID)
    ):
        asyncio.create_task(
            ALT_STATUS_CHANNEL.send(
                content=f"<t:{round(time())}:R><@&1288980643061170188>",
                embed=embed,
            )
        )

    if (
        user_game_info[4] != presence.userPresenceType
        and not message_sent
        and bot.tracking.get(presence.userId)
    ):
        try:
            await bot.tracking[presence.userId][0].send(
                content=f"<t:{round(time())}:R>{"".join(bot.tracking[presence.userId][1])}",
                embed=embed,
            )
        except Exception as e:
            logger.exception(e)

    user_game_info[4] = presence.userPresenceType

    should_send = (
        (
            presence.userPresenceType == 2
            and (presence.gameId in [GAME_ID, None] or not bot.OtherGame)
            and not bot.MuteAll
        )
        or (presence.userPresenceType == 1 and not (bot.OnlineMuted or bot.MuteAll))
        or (presence.userPresenceType == 0 and not (bot.OfflineMuted or bot.MuteAll))
    )

    if should_send:
        if not presence.groupName in embeds:
            embeds[presence.groupName] = [
                presence.userPresenceType == 2
                and (
                    presence.gameId == None
                    or (presence.gameId == GAME_ID and not presence.placeId == GAME_ID)
                ),
            ]
            embeds[presence.groupName].append(embed)
            return

        if not presence.groupName == "None":
            if embeds[presence.groupName][1] == False:
                embeds[presence.groupName][1] = presence.userPresenceType == 2 and (
                    presence.gameId == None
                    or (presence.gameId == GAME_ID and not presence.placeId == GAME_ID)
                )
            return

        embeds[presence.groupName].append(
            presence.userPresenceType == 2
            and (
                presence.gameId == None
                or (presence.gameId == GAME_ID and not presence.placeId == GAME_ID)
            )
        )

        embeds[presence.groupName].append(embed)


async def user_status(
    userPresences: RobloxPy.Presence.Presences.UserPresenceGroup,
    bot,
    STATUS_CHANNEL,
    ALT_STATUS_CHANNEL,
):
    embeds = {}

    tasks = []
    for presence in userPresences.presences:
        tasks.append(
            asyncio.create_task(
                manage_data_create_embed(presence, bot, embeds, ALT_STATUS_CHANNEL)
            )
        )

    await asyncio.gather(*tasks)

    for groupName, Embeds in embeds.items():
        if groupName != "None":
            SubGroups = [Embeds[i : i + 10] for i in range(0, len(Embeds), 10)]
            for group in SubGroups:
                await STATUS_CHANNEL.send(
                    content=f"<t:{round(time())}:R>"
                    + ("<@&1288980643061170188>" if group[0] else ""),
                    embeds=group[1:],
                )

    if embeds.get("None"):
        for i, embed in enumerate(embeds["None"]):
            if not (i % 2) == 0:
                await STATUS_CHANNEL.send(
                    content=f"<t:{round(time())}:R>"
                    + ("<@&1288980643061170188>" if embeds["None"][i - 1] else ""),
                    embed=embed,
                )
