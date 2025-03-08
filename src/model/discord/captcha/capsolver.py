import asyncio
from typing import Tuple, Any
from curl_cffi.requests import AsyncSession
from loguru import logger


class Capsolver:
    def __init__(
        self, account_index: int, api_key: str, session: AsyncSession, proxy: str
    ):
        self.account_index = account_index
        self.api_key = api_key
        self.session = AsyncSession()
        self.proxy = proxy

    async def solve_hcaptcha(
        self, url: str, captcha_rqdata: str, site_key: str, user_agent: str
    ) -> Tuple[str, bool]:
        """
        Solve HCaptcha using Capsolver service
        Returns: Tuple[gRecaptchaResponse: str, success: bool]
        """
        try:
            if not self.proxy:
                logger.error(
                    f"{self.account_index} | Capsolver requires proxy for solving HCaptcha."
                )
                return "", False

            # Parse proxy string format user:pass@ip:port
            proxy_user, proxy_pass = self.proxy.split("@")[0].split(":")
            proxy_ip, proxy_port = self.proxy.split("@")[1].split(":")

            captcha_data = {
                "clientKey": self.api_key,
                "task": {
                    "type": "HCaptchaTurboTask",
                    "websiteURL": url,
                    "websiteKey": site_key,
                    "isInvisible": False,
                    "enterprisePayload": {"rqdata": captcha_rqdata},
                    "proxy": f"http:{proxy_ip}:{proxy_port}:{proxy_user}:{proxy_pass}",
                    "userAgent": user_agent,
                },
            }

            response = await self.session.post(
                "https://api.capsolver.com/createTask", json=captcha_data
            )

            if response.status_code == 200:
                logger.info(f"{self.account_index} | Starting to solve hcaptcha...")
                return await self.get_captcha_result(response.json()["taskId"])
            else:
                logger.error(
                    f"{self.account_index} | Failed to send hcaptcha request: {response.json()['errorDescription']}"
                )
                return "", False

        except Exception as err:
            logger.error(
                f"{self.account_index} | Failed to send hcaptcha request to Capsolver: {err}"
            )
            return "", False

    async def get_captcha_result(self, task_id: str) -> Tuple[Any, bool]:
        """
        Get captcha solution result
        Returns: Tuple[gRecaptchaResponse: str, success: bool]
        """
        for _ in range(30):
            try:
                response = await self.session.post(
                    "https://api.capsolver.com/getTaskResult",
                    json={"clientKey": self.api_key, "taskId": task_id},
                )

                if response.status_code == 200:
                    result = response.json()

                    if result["errorId"] != 0:
                        logger.error(f"{self.account_index} | Hcaptcha failed!")
                        return "", False

                    if result["status"] == "ready":
                        logger.success(f"{self.account_index} | Hcaptcha solved!")
                        return result["solution"]["gRecaptchaResponse"], True

            except Exception as err:
                logger.error(
                    f"{self.account_index} | Failed to get hcaptcha solution: {err}"
                )
                return "", False

            # Sleep between result requests
            await asyncio.sleep(7)

        logger.error(f"{self.account_index} | Failed to get hcaptcha solution")
        return "", False
