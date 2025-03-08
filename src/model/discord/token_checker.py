import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession

from src.utils.config import Config
from src.utils.constants import Account
from src.model.discord.get_account_info import get_account_info
from src.utils.writer import update_account


async def token_checker(account: Account, config: Config, client: AsyncSession) -> tuple[bool, str] | bool:
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                guilds_url = "https://discord.com/api/v9/users/@me/affinities/guilds"
                me_url = "https://discord.com/api/v9/users/@me"

                resp = await client.get(guilds_url, headers={"Authorization": f"{account.token}"})

                if resp.status_code in (401, 403):
                    logger.warning(f"{account.index} | Token is locked: {account.token}")
                    return True, "locked"

                if resp.status_code in (200, 204):
                    response = await client.get(me_url, headers={"Authorization": f"{account.token}"})
                    flags_data = response.json()['flags'] - response.json()['public_flags']
                    if flags_data == 17592186044416:
                        logger.warning(f"{account.index} | Token is quarantined: {account.token}")
                        await update_account(account.token, "STATUS", "QUARANTINED")

                        return False, "quarantined"
                    elif flags_data == 1048576:
                        logger.warning(f"{account.index} | Token is flagged as spammer: {account.token}")
                        await update_account(account.token, "STATUS", "SPAMMER")
                        
                    elif flags_data == 17592186044416 + 1048576:
                        logger.warning(f"{account.index} | Token is flagged as spammer and quarantined: {account.token}")
                        await update_account(account.token, "STATUS", "SPAMMER AND QUARANTINED")

                    logger.success(f"{account.index} | Token is working!")
                    await update_account(account.token, "STATUS", "OK")

                    if response.json()['username']:
                        try:
                            await update_account(account.token, "USERNAME", response.json()['username'])
                        except Exception as e:
                            logger.error(f"{account.index} | Error updating username: {e}")

                else:
                    logger.error(f"{account.index} | Invalid status code {resp.status_code} while checking token.")

                return True, ""
            except Exception as err:
                random_sleep = random.randint(config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0], config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1])
                logger.error(f"{account.index} | Failed to check token status: {err}. Retrying in {random_sleep} seconds...")
                await asyncio.sleep(random_sleep)
        
        await update_account(account.token, "STATUS", "UNKNOWN")
        return False, ""
