import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession 

from src.utils.config import Config
from src.utils.constants import Account
from src.model.discord.get_account_info import get_account_info


async def get_all_servers(account: Account, config: Config, session: AsyncSession):
    for retry in range(config.SETTINGS.ATTEMPTS):
        try:
            account_info = await get_account_info(account, config, session)
            if account_info is None:
                raise Exception("Failed to get account info")

            all_guilds_url = (
                f"https://discord.com/api/v9/users/{account_info.id}/profile"
            )

            headers = {
                "Authorization": account.token,
                "referer": "https://discord.com/channels/@me",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
            }

            response = await session.get(all_guilds_url, headers=headers)
            token_guilds = response.json()["mutual_guilds"]

            all_guilds_message = ""

            for guild in token_guilds:
                for x in range(3):
                    try:
                        guild_name = await session.get(
                            f"https://discord.com/api/v9/guilds/{guild['id']}",
                            headers=headers,
                        )

                        guild_name = guild_name.json()["name"]
                        all_guilds_message += f"{guild_name} | "
                        break
                    except Exception as err:
                        await asyncio.sleep(3)
                        if x == 2:
                            raise Exception(f"unable to get guild name: {err}")

            logger.success(
                f"{account.index} | {account.token} | {account_info.username} | {len(token_guilds)} Guilds: {all_guilds_message}"
            )
            return True

        except Exception as e:
            random_pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"[{account.index}] | Error in get_all_servers: {e}. Pausing for {random_pause} seconds."
            )
            await asyncio.sleep(random_pause)

    return False

async def check_if_token_in_guild(account: Account, config: Config, session: AsyncSession):
    for retry in range(config.SETTINGS.ATTEMPTS):
        try:
            account_info = await get_account_info(account, config, session)
            if account_info is None:
                raise Exception("Failed to get account info")

            all_guilds_url = (
                f"https://discord.com/api/v9/users/{account_info.id}/profile"
            )

            headers = {
                "Authorization": account.token,
                "referer": "https://discord.com/channels/@me",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
            }

            response = await session.get(all_guilds_url, headers=headers)
            token_guilds = response.json()["mutual_guilds"]

            all_guilds_id = [guild["id"] for guild in token_guilds]

            if config.DATA_FOR_TASKS.IF_TOKEN_IN_GUILD_ID in all_guilds_id:
                logger.success(f"{account.index} | {account.token} | {account_info.username} | Token is in the guild {config.DATA_FOR_TASKS.IF_TOKEN_IN_GUILD_ID}")
                return True
            else:
                logger.warning(f"{account.index} | {account.token} | {account_info.username} | Token is not in the guild {config.DATA_FOR_TASKS.IF_TOKEN_IN_GUILD_ID}")
                return False

        except Exception as e:
            random_pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(f"[{account.index}] | Error in check_if_token_in_guild: {e}. Pausing for {random_pause} seconds.")
            await asyncio.sleep(random_pause)
    return False

