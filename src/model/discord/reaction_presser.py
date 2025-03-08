import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession
from urllib.parse import quote

from src.utils.config import Config
from src.utils.constants import Account


async def reaction_presser(account: Account, config: Config, session: AsyncSession):
    if config.DATA_FOR_TASKS is None or config.DATA_FOR_TASKS.EMOJIS_INFO is None:
        logger.error(f"No emojis info found.")
        return False

    for emoji in config.DATA_FOR_TASKS.EMOJIS_INFO:
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                result = await press_reaction(account, config, session, emoji, config.DATA_FOR_TASKS.REACTION_CHANNEL_ID, config.DATA_FOR_TASKS.REACTION_MESSAGE_ID)
                if result is None:
                    return False
                elif not result:
                    continue
                else:
                    random_sleep = random.randint(config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0], config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1])
                    await asyncio.sleep(random_sleep)
                    break

            except Exception as e:
                random_sleep = random.randint(config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0], config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1])
                logger.error(f"{account.index} | Error: {e}. Retrying in {random_sleep} seconds...")
                await asyncio.sleep(random_sleep)
    return False


async def press_reaction(account: Account, config: Config, session: AsyncSession, emoji: dict, channel_id: str, message_id: str):
    try:
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': account.token,
            'Referer': 'https://discord.com/channels/1343982282566013048/1343982282566013051',
            'X-Debug-Options': 'bugReporterEnabled',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'X-Discord-Timezone': 'Etc/GMT-2',
            'X-Super-Properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InJ1IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMy4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMzLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tLyIsInJlZmVycmluZ19kb21haW4iOiJkaXNjb3JkLmNvbSIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozNzQ2NzksImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImhhc19jbGllbnRfbW9kcyI6ZmFsc2V9',
            'X-Discord-Locale': 'en-US',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        params = {
            'location': 'Message Context Menu',
            'type': '0',
        }

        if emoji['id'] is not None:
            emoji_name = emoji['name']
            resp = await session.put(
                f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}%3A{emoji['id']}/%40me",
                headers=headers,
                params=params,
            )
        else:
            emoji_name = quote(emoji['name'])
            resp = await session.put(
                f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}/%40me",
                headers=headers,
                params=params,
            )


        if 'Unauthorized' in resp.text:
            logger.error(f"{account.index} | Incorrect discord token or your account is blocked.")
            return None
        
        if resp.status_code == 204:
            logger.success(f"{account.index} | Successfully reacted to the message!")
            return True

    except Exception as e:
        random_sleep = random.randint(config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0], config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1])
        logger.error(f"{account.index} | Error: {e}. Retrying in {random_sleep} seconds...")
        await asyncio.sleep(random_sleep)
        return False
