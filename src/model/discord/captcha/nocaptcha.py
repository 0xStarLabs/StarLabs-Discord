import json
from typing import Optional, Tuple
from curl_cffi.requests import AsyncSession
from loguru import logger


class NoCaptcha:
    API_URL = "http://api.nocaptcha.io/api/wanda/discord/guild"

    def __init__(self, user_token: str, session: AsyncSession):
        self.user_token = user_token
        self.session = session

    async def solve_discord_invite(
        self, discord_token: str, invite_code: str = None, guild_id: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Solve Discord captcha using noCaptcha service

        Args:
            discord_token: Discord account token
            invite_code: Discord invite code (guild_name)
            guild_id: Discord guild ID

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            headers = {
                "User-Token": self.user_token,
                "Content-Type": "application/json",
            }

            # Prepare request data
            json_data = {"authorization": discord_token}

            if invite_code:
                json_data["guild_name"] = invite_code
            elif guild_id:
                json_data["guild_id"] = guild_id
            else:
                return False, "Either invite_code or guild_id must be provided"

            response = await self.session.post(
                self.API_URL, headers=headers, json=json_data
            )

            if response.status_code != 200:
                return (
                    False,
                    f"API request failed with status code: {response.status_code}",
                )

            result = response.json()

            if result["status"] != 1:
                return False, result.get("msg", "Unknown error")

            logger.success(f"Captcha solved successfully! Cost: {result['cost']}")
            return True, None

        except Exception as e:
            error_msg = f"NoCaptcha error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def solve_hcaptcha(
        self,
        sitekey: str,
        referer: str,
        rqdata: str = None,
        domain: str = "hcaptcha.com",
        proxy: str = None,
        region: str = None,
        invisible: bool = False,
        need_ekey: bool = False,
    ) -> dict | None:
        """
        Solve hCaptcha using noCaptcha service

        Args:
            sitekey: hCaptcha integration key
            referer: Trigger page address (full URL)
            rqdata: Optional captcha_rqdata or captcha_rqtoken
            domain: hCaptcha verification API domain
            proxy: Optional proxy in format ip:port or usr:pwd@ip:port or socks5://ip:port
            region: Proxy region (e.g., 'hk', 'sg') - required if proxy is provided
            invisible: Whether the captcha is invisible
            need_ekey: Whether to return E0 key

        Returns:
            dict | None: response_data
        """
        try:
            API_URL = "http://api.nocaptcha.io/api/wanda/hcaptcha/universal"

            headers = {
                "User-Token": self.user_token,
                "Content-Type": "application/json",
            }

            # Prepare request data
            json_data = {
                "sitekey": sitekey,
                "referer": referer,
                "domain": domain,
                "invisible": invisible,
                "need_ekey": need_ekey,
            }

            # Add optional parameters if provided
            if rqdata:
                json_data["rqdata"] = rqdata
            if proxy:
                json_data["proxy"] = proxy
                if not region:
                    raise Exception("Region is required when using proxy")
                json_data["region"] = region

            response = await self.session.post(API_URL, headers=headers, json=json_data)

            if response.status_code != 200:
                raise Exception(
                    f"API request failed with status code: {response.status_code}"
                )

            result = response.json()

            if result["status"] != 1:
                raise Exception(result.get("msg", "Unknown error"))

            logger.success(f"hCaptcha solved successfully! Cost: {result['cost']}")

            return {
                "id": result.get("id"),
                "generated_pass_UUID": result.get("data", {}).get(
                    "generated_pass_UUID"
                ),
                "ekey": result.get("data", {}).get("ekey"),
                "cost": result.get("cost"),
            }

        except Exception as e:
            error_msg = f"NoCaptcha hCaptcha error: {str(e)}"
            logger.error(error_msg)
            return None
