import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession

from .utils import calculate_nonce, create_x_super_properties
from src.utils.config import Config
from src.utils.constants import Account
from src.utils.writer import update_account


async def message_sender(account: Account, config: Config, session: AsyncSession) -> bool:
    try:
        if config.MESSAGE_SENDER.SEND_MESSAGES_RANDOMLY:
            random.shuffle(account.messages_to_send)

        for message_number in range(config.MESSAGE_SENDER.NUMBER_OF_MESSAGES_TO_SEND):
            for retry in range(config.SETTINGS.ATTEMPTS):
                try:
                    if config.MESSAGE_SENDER.SEND_MESSAGES_RANDOMLY:
                        message_to_send = random.choice(account.messages_to_send)
                    else:
                        message_to_send = account.messages_to_send[message_number]

                    message_id = await send_chat_message(account, config, session, config.MESSAGE_SENDER.GUILD_ID, config.MESSAGE_SENDER.CHANNEL_ID, message_to_send)
                    
                    logger.info(f"{account.index} | Message {message_id} sent successfully.")

                    if config.MESSAGE_SENDER.DELETE_MESSAGE_INSTANTLY:
                        await delete_message(account, config, session, config.MESSAGE_SENDER.GUILD_ID, config.MESSAGE_SENDER.CHANNEL_ID, message_id)
                        logger.info(f"{account.index} | Message {message_id} deleted successfully.")

                    random_sleep = random.randint(config.MESSAGE_SENDER.PAUSE_BETWEEN_MESSAGES[0], config.MESSAGE_SENDER.PAUSE_BETWEEN_MESSAGES[1])
                    logger.info(f"{account.index} | Waiting {random_sleep} seconds before next message...")
                    await asyncio.sleep(random_sleep)   
                    break

                except Exception as e:
                    random_sleep = random.randint(config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0], config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1])
                    logger.error(f"{account.index} | Error sending chat message ({message_number}): {e}. Retrying in {random_sleep} seconds...")
                    await asyncio.sleep(random_sleep)
                    
    except Exception as e:
        logger.error(f"{account.index} | Error sending chat message: {e}")
        return False
    

async def send_chat_message(account: Account, config: Config, session: AsyncSession, server_id: str, channel_id: str, message: str) -> str:
    for retry in range(config.SETTINGS.ATTEMPTS):
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,zh-TW;q=0.6,zh;q=0.5',
                'authorization': account.token,
                'content-type': 'application/json',
                'origin': 'https://discord.com',
                'priority': 'u=1, i',
                'referer': f'https://discord.com/channels/{server_id}/{channel_id}',
                'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-locale': 'en-US',
                'x-discord-timezone': 'Etc/GMT-2',
                'x-super-properties': create_x_super_properties(),
            }

            json_data = {
                'mobile_network_type': 'unknown',
                'content': message,
                'nonce': calculate_nonce(),
                'tts': False,
                'flags': 0,
            }

            response = await session.post(
                f'https://discord.com/api/v9/channels/{channel_id}/messages',
                headers=headers,
                json=json_data,
            )

            if response.status_code == 200:
                logger.success(f"{account.index} | Message sent successfully.")
                return response.json()['id']
            else:
                raise Exception(response.text)

        except Exception as e:
            random_sleep = random.randint(config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0], config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1])
            logger.error(f"{account.index} | Error sending chat message: {e}. Retrying in {random_sleep} seconds...")
            await asyncio.sleep(random_sleep)

    return None

async def delete_message(account: Account, config: Config, session: AsyncSession, server_id: str, channel_id: str, message_id: str) -> bool:
    for retry in range(config.SETTINGS.ATTEMPTS):
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,zh-TW;q=0.6,zh;q=0.5',
                'authorization': account.token,
                'origin': 'https://discord.com',
                'priority': 'u=1, i',
                'referer': f'https://discord.com/channels/{server_id}/{channel_id}',
                'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-locale': 'en-US',
                'x-discord-timezone': 'Etc/GMT-2',
                'x-super-properties': create_x_super_properties(),
                }

            response = await session.delete(
                f'https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}',
                headers=headers,
            )

            if response.status_code == 204:
                logger.success(f"{account.index} | Message deleted successfully.")
                return True
            else:
                raise Exception(response.text)

        except Exception as e:
            logger.error(f"{account.index} | Error deleting message: {e}")

    return False

