import asyncio
from dataclasses import dataclass
import random
from loguru import logger
from curl_cffi.requests import AsyncSession 
from src.utils.config import Config
from src.utils.constants import Account


@dataclass
class AccountInfo:
    id: str
    username: str
    global_name: str
    email: str
    verified: bool
    phone: str
    bio: str


async def get_account_info(
    account: Account, config: Config, session: AsyncSession
) -> AccountInfo | None:
    for retry in range(config.SETTINGS.ATTEMPTS):
        try:
            headers = {
                "Authorization": account.token,
                "referer": "https://discord.com/channels/@me",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
            }

            response = await session.get(
                "https://discord.com/api/v9/users/@me", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get account info: {response.status_code} | {response.text}"
                )

            data = response.json()

            account_info = AccountInfo(
                id=data["id"],
                username=data["username"],
                global_name=data["global_name"],
                email=data["email"],
                verified=data["verified"],
                phone=data["phone"],
                bio=data["bio"],
            )

            logger.success(
                f"[{account.index}] | Got account info for {account_info.username}"
            )
            return account_info

        except Exception as e:
            random_pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"[{account.index}] | Error in get_account_info: {e}. Pausing for {random_pause} seconds."
            )
            await asyncio.sleep(random_pause)

    return None
