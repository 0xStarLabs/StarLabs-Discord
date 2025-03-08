import asyncio
from dataclasses import dataclass
import random
from loguru import logger
from curl_cffi.requests import AsyncSession 
from src.model.discord.utils import calculate_nonce, create_x_super_properties
from src.utils.config import Config
from src.utils.constants import Account




async def press_button(account: Account, config: Config, session: AsyncSession):
    for retry in range(config.SETTINGS.ATTEMPTS):
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,zh-TW;q=0.6,zh;q=0.5',
                'authorization': account.token,
                'content-type': 'application/json',
                'origin': 'https://discord.com',
                'priority': 'u=1, i',
                'referer': f'https://discord.com/channels/{config.DATA_FOR_TASKS.BUTTON_PRESSER_GUILD_ID}/{config.DATA_FOR_TASKS.BUTTON_PRESSER_CHANNEL_ID}',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-locale': 'en-US',
                'x-discord-timezone': 'Etc/GMT-2',
                'x-super-properties': create_x_super_properties(),
                }

            json_data = {
                'type': 3,
                'nonce': calculate_nonce(),
                'guild_id': config.DATA_FOR_TASKS.BUTTON_PRESSER_GUILD_ID,
                'channel_id': config.DATA_FOR_TASKS.BUTTON_PRESSER_CHANNEL_ID,
                'message_flags': 0,
                'message_id': config.DATA_FOR_TASKS.BUTTON_PRESSER_MESSAGE_ID,
                'application_id': config.DATA_FOR_TASKS.BUTTON_PRESSER_APPLICATION_ID,
                'session_id': 'd734d6e7368c1d5de4cd76043fee2e55',
                'data': {
                    'component_type': config.DATA_FOR_TASKS.BUTTON_PRESSER_BUTTON_DATA['type'],
                    'custom_id': config.DATA_FOR_TASKS.BUTTON_PRESSER_BUTTON_DATA['custom_id'],
                },
            }

            response = await session.post('https://discord.com/api/v9/interactions', headers=headers, json=json_data)
            if response.status_code != 204:
                raise Exception(f"Failed to press button: {response.status_code} | {response.text}")
            else:
                logger.success(f"[{account.index}] | Button pressed successfully")
                return True 
        
        except Exception as e:
            random_pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(f"[{account.index}] | Error in press_button: {e}. Pausing for {random_pause} seconds.")
            await asyncio.sleep(random_pause)
    return False

