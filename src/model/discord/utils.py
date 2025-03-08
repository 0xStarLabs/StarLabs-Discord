import base64
import json
import time

from loguru import logger
from curl_cffi.requests import AsyncSession, Response

from src.utils.constants import Account

def calculate_nonce() -> str:
    unix_ts = time.time()
    return str((int(unix_ts) * 1000 - 1420070400000) * 4194304)


def create_x_super_properties() -> str:
    return base64.b64encode(json.dumps({
   "os":"Windows",
   "browser":"Chrome",
   "device":"",
   "system_locale":"ru",
   "browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
   "browser_version":"133.0.0.0",
   "os_version":"10",
   "referrer":"https://discord.com/",
   "referring_domain":"discord.com",
   "referrer_current":"",
   "referring_domain_current":"",
   "release_channel":"stable",
   "client_build_number":370533,
   "client_event_source":None,
   "has_client_mods":False
}, separators=(',', ':')).encode('utf-8')).decode('utf-8')


async def get_guild_ids(client: AsyncSession, invite_code: str, account: Account) -> tuple[str, str, bool]:
    try:
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'{account.token}',
            'Referer': f'https://discord.com/invite/{invite_code}',
            'X-Debug-Options': 'bugReporterEnabled',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="131", "Chromium";v="131"',
            'sec-ch-ua-mobile': '?0',
            'X-Discord-Timezone': 'Etc/GMT-2',
            'X-Super-Properties': create_x_super_properties(),
            'X-Discord-Locale': 'en-US',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        params = {
            'with_counts': 'true',
            'with_expiration': 'true',
            'with_permissions': 'false',
        }

        response = await client.get(f'https://discord.com/api/v9/invites/{invite_code}', params=params, headers=headers)
        
        if "You need to verify your account" in response.text:
            logger.error(f"{account.index} | Account needs verification (Email code etc).")
            return "verification_failed", "", False

        location_guild_id = response.json()['guild_id']
        location_channel_id = response.json()['channel']['id']

        return location_guild_id, location_channel_id, True

    except Exception as err:
        logger.error(f"{account.index} | Failed to get guild ids: {err}")
        return None, None, False
    

def create_x_context_properties(location_guild_id: str, location_channel_id: str) -> str:
    return base64.b64encode(json.dumps({
        "location": "Accept Invite Page",
        "location_guild_id": location_guild_id,
        "location_channel_id": location_channel_id,
        "location_channel_type": 0
    }, separators=(',', ':')).encode('utf-8')).decode('utf-8')


async def init_cf(account: Account, client: AsyncSession) -> bool:
    try:
        resp = await client.get("https://discord.com/login",
                          headers={
                              'authority': 'discord.com',
                              'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                              'accept-language': 'en-US,en;q=0.9',
                              'sec-ch-ua': '"Chromium";v="131", "Not A(Brand";v="24", "Google Chrome";v="131"',
                              'sec-ch-ua-mobile': '?0',
                              'sec-ch-ua-platform': '"Windows"',
                              'sec-fetch-dest': 'document',
                              'sec-fetch-mode': 'navigate',
                              'sec-fetch-site': 'none',
                              'sec-fetch-user': '?1',
                              'upgrade-insecure-requests': '1',
                          }
                          )

        if await set_response_cookies(client, resp):
            logger.success(f"{account.index} | Initialized new cookies.")
            return True
        else:
            logger.error(f"{account.index} | Failed to initialize new cookies.")
            return False

    except Exception as err:
        logger.error(f"{account.index} | Failed to initialize new cookies: {err}")
        return False


async def set_response_cookies(client: AsyncSession, response: Response) -> bool:
    try:
        cookies = response.headers.get_list("set-cookie")
        for cookie in cookies:
            try:
                key, value = cookie.split(';')[0].strip().split("=")
                client.cookies.set(name=key, value=value, domain="discord.com", path="/")

            except:
                pass

        return True

    except Exception as err:
        logger.error(f"Failed to set response cookies: {err}")
        return False
