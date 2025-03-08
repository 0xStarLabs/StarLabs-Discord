import asyncio
import random
import aiohttp
from loguru import logger

from src.utils.config import Config
from src.utils.constants import Account


async def leave_guild(account: Account, config: Config, guild_id: str) -> bool:
    for retry in range(config.SETTINGS.ATTEMPTS):
        """
        Leave Discord guild

        Args:
            token: Discord token
            guild_id: ID of guild to leave
            proxy: Proxy in format user:pass@ip:port
        """
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "Authorization": account.token,
            "X-Debug-Options": "bugReporterEnabled",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "X-Discord-Timezone": "Etc/GMT-2",
            "X-Discord-Locale": "en-US",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
        }

        try:
            # Настраиваем прокси с аутентификацией
            if account.proxy:
                proxy_auth = None
                if "@" in account.proxy:
                    auth, proxy = account.proxy.split("@")
                    user, pwd = auth.split(":")
                    proxy_auth = aiohttp.BasicAuth(user, pwd)
                    proxy_url = f"http://{proxy}"
                else:
                    proxy_url = f"http://{account.proxy}"
            else:
                proxy_url = None
                proxy_auth = None

            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"https://discord.com/api/v9/users/@me/guilds/{guild_id}",
                    headers=headers,
                    json={"lurking": False},  # Этот параметр иногда требуется Discord
                    proxy=proxy_url,
                    proxy_auth=proxy_auth,
                    ssl=False,  # Отключаем SSL для работы с прокси
                ) as response:

                    if response.status in [
                        200,
                        204,
                    ]:  # Discord может вернуть оба эти статуса при успехе
                        logger.success(
                            f"{account.index} | Successfully left guild {guild_id}"
                        )
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"{account.index} | Failed to leave guild {guild_id}. Status: {response.status}, Response: {error_text}"
                        )
                        return False

        except Exception as e:
            random_pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{account.index} | Error while leaving guild {guild_id}: {str(e)}. Pausing for {random_pause} seconds."
            )
            await asyncio.sleep(random_pause)

    return False
