from time import time

import discord
from discord import app_commands
from loguru import logger

import RobloxPy
from config.command_description import FriendsDesc
from config.constants import GAME_ID
from config.embeds import error_embed, format_user_embed
from utils.exceptions import UserNotFound


@app_commands.command(name="ingame", description=FriendsDesc.ingame)
@app_commands.describe(sameserver=FriendsDesc.sameServer, username=FriendsDesc.username)
async def ingame(interaction: discord.Interaction, username: str, sameserver: bool):
    logger.log(
        "COMMAND",
        f"{interaction.user.name} used {interaction.command.name} command",
    )

    try:
        user_presence, user = await RobloxPy.Presence.get_presence_from_username(
            username
        )

        user = user.get_by_requested_username(username)
        user_presence = user_presence.get_by_userid(user.userId)

        if not user:
            raise UserNotFound(username)

        if user_presence != user_presence:
            await interaction.response.send_message(
                "User is not in a game", ephemeral=True
            )
            return

        friends = await user.get_friends()
        presences = await RobloxPy.Presence.get_presence(*friends)
        presences.filter_by_presence_types(2)
        presences.filter_by_gameids(GAME_ID, None)

        if len(presences) < 1:
            await interaction.response.send_message(
                "No friends in-game found.", ephemeral=True
            )
            return

        friends_users = RobloxPy.Users.get_users_by_userid(*presences.userIds)

        embeds = []
        for presence in presences.presences:
            if not sameserver or (sameserver and (presence == user_presence)):
                embeds.append(
                    format_user_embed(
                        presenceType=presence.userPresenceType,
                        username=friends_users.get_by_userid(presence.userId).username,
                        game=presence.lastlocation,
                        lobby=(
                            ("True" if presence.placeId == presence.gameId else "False")
                            if presence.gameId
                            else None
                        ),
                        jobId=presence.jobId,
                    )
                )

        if embeds:
            embedGroups = [
                [embed for embed in embeds[i : i + 10]]
                for i in range(0, len(embeds), 10)
            ]
            for i, embedGroup in enumerate(embedGroups):
                if i != 0:
                    await interaction.followup.send(
                        content=f"<t:{int(time())}:R>", embeds=embedGroup
                    )
                else:
                    await interaction.response.send_message(
                        content=f"<t:{int(time())}:R>", embeds=embedGroup
                    )
        else:
            await interaction.response.send_message(
                "No friends in-game found.", ephemeral=True
            )

    except Exception as e:
        logger.exception(e)
        await interaction.response.send_message(embed=error_embed(e))
