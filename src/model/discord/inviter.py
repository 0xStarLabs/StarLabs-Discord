import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession
from src.model.discord.captcha.capsolver import Capsolver
from src.model.discord.utils import (
    create_x_context_properties,
    create_x_super_properties,
    get_guild_ids,
    init_cf,
)
from src.utils.config import Config
from src.utils.constants import DISCORD_CAPTCHA_SITEKEY, Account
from src.model.discord.captcha import NoCaptcha


class Inviter:
    def __init__(self, account: Account, config: Config, session: AsyncSession):
        self.account = account
        self.config = config
        self.session = session

    async def invite(self, invite_code: str) -> dict:
        for retry in range(self.config.SETTINGS.ATTEMPTS):
            try:
                if not await init_cf(self.account, self.session):
                    raise Exception("Failed to initialize cf")

                guild_id, channel_id, success = await get_guild_ids(
                    self.session, invite_code, self.account
                )
                if not success:
                    continue

                result = await self.send_invite_request(
                    invite_code, guild_id, channel_id
                )
                if result is None:
                    return None
                elif result:
                    return True
                else:
                    continue
                
            except Exception as e:
                random_sleep = random.randint(
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
                )
                logger.error(
                    f"{self.account.index} | Error: {e}. Retrying in {random_sleep} seconds..."
                )
                await asyncio.sleep(random_sleep)
        return False

    async def send_invite_request(
        self, invite_code: str, guild_id: str, channel_id: str
    ) -> bool:
        for retry in range(self.config.SETTINGS.ATTEMPTS):
            try:
                # nocaptcha = NoCaptcha(
                #     user_token=self.config.INVITER.NOCAPTCHA_API_KEY,
                #     session=self.session,
                # )
                # success, error = await nocaptcha.solve(
                #     discord_token=self.account.token, guild_id=guild_id
                # )

                # if success:
                #     # Continue with join process
                #     pass
                # else:
                #     if "错误的令牌" in str(error):
                #         logger.error(f"Captcha solving failed: wrong NoCaptcha API key.")
                #         return None
                #     else:
                #         logger.error(f"Captcha solving failed: {error}")
                #         return False

                headers = {
                    "accept": "*/*",
                    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,zh-TW;q=0.6,zh;q=0.5",
                    "authorization": f"{self.account.token}",
                    "content-type": "application/json",
                    "origin": "https://discord.com",
                    "priority": "u=1, i",
                    "referer": f"https://discord.com/invite/{invite_code}",
                    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="131", "Chromium";v="131"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "x-context-properties": create_x_context_properties(
                        guild_id, channel_id
                    ),
                    "x-debug-options": "bugReporterEnabled",
                    "x-discord-locale": "en-US",
                    "x-discord-timezone": "Etc/GMT-2",
                    "x-super-properties": create_x_super_properties(),
                }

                json_data = {
                    "session_id": None,
                }

                response = await self.session.post(
                    f"https://discord.com/api/v9/invites/{invite_code}",
                    headers=headers,
                    json=json_data,
                )

                if (
                    "You need to update your app to join this server." in response.text
                    or "captcha_rqdata" in response.text
                ):
                    logger.error(f"{self.account.index} | Captcha detected. Can't solve it.")
                    return None

                    # nocaptcha = NoCaptcha(
                    #     user_token=self.config.INVITER.NOCAPTCHA_API_KEY,
                    #     session=self.session,
                    # )
                    # success, error = await nocaptcha.solve(
                    #     discord_token=self.account.token, guild_id=guild_id
                    # )

                    # if success:
                    #     # Continue with join process
                    #     pass
                    # else:
                    #     logger.error(f"Captcha solving failed: {error}")

                elif response.status_code == 200 and response.json()["type"] == 0:
                    logger.success(f"{self.account.index} | Account joined the server!")
                    return True

                elif "Unauthorized" in response.text:
                    logger.error(
                        f"{self.account.index} | Incorrect discord token or your account is blocked."
                    )
                    return False

                elif "You need to verify your account in order to" in response.text:
                    logger.error(
                        f"{self.account.index} | Account needs verification (Email code etc)."
                    )
                    return False

                else:
                    logger.error(
                        f"{self.account.index} | Unknown error: {response.text}"
                    )

            except Exception as e:
                random_sleep = random.randint(
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
                )
                logger.error(
                    f"{self.account.index} | Send invite error: {e}. Retrying in {random_sleep} seconds..."
                )
                await asyncio.sleep(random_sleep)

        return False
