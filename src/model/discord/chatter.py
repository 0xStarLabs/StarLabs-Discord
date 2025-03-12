import asyncio
from dataclasses import dataclass
from loguru import logger
import random
from curl_cffi.requests import AsyncSession


from src.model.discord.utils import calculate_nonce
from src.utils.config import Config
from src.model.gpt import ask_chatgpt
from src.model.gpt.prompts import (
    BATCH_MESSAGES_SYSTEM_PROMPT,
    REFERENCED_MESSAGES_SYSTEM_PROMPT,
)
from src.utils.constants import Account


@dataclass
class ReceivedMessage:
    """Represents a message received from Discord"""

    type: int
    content: str
    message_id: str
    channel_id: str
    author_id: str
    author_username: str
    referenced_message_content: str
    referenced_message_author_id: str


class DiscordChatter:
    def __init__(
        self,
        account: Account,
        client: AsyncSession,
        config: Config,
    ):
        self.account = account
        self.client = client
        self.config = config

        self.my_account_id: str = ""
        self.my_account_username: str = ""
        self.my_replies_messages: list = []

    async def start_chatting(self) -> bool:
        number_of_messages_to_send = random.randint(
            self.config.AI_CHATTER.MESSAGES_TO_SEND_PER_ACCOUNT[0],
            self.config.AI_CHATTER.MESSAGES_TO_SEND_PER_ACCOUNT[1],
        )
        for message_index in range(number_of_messages_to_send):
            for retry_index in range(self.config.SETTINGS.ATTEMPTS):
                try:
                    message_sent = False
                    replied_to_me = False

                    last_messages = await self._get_last_chat_messages(
                        self.config.AI_CHATTER.GUILD_ID,
                        self.config.AI_CHATTER.CHANNEL_ID,
                    )
                    logger.info(
                        f"{self.account.index} | Last messages: {len(last_messages)} "
                    )

                    if self.my_account_id:
                        # First check if anyone replied to our messages
                        replies_to_me = [
                            msg
                            for msg in last_messages
                            if msg.referenced_message_author_id == self.my_account_id
                            and msg.message_id
                            not in self.my_replies_messages  # Don't reply to messages we've already replied to
                            and msg.author_username
                            != self.my_account_username  # Don't reply to our own messages
                        ]

                        if replies_to_me:
                            # Check if we should answer based on answer_percentage
                            should_answer = (
                                random.random() * 100
                            ) < self.config.AI_CHATTER.ANSWER_PERCENTAGE

                            if should_answer:
                                # Someone replied to us - let's reply back
                                message = random.choice(replies_to_me)
                                logger.info(
                                    f"{self.account.index} | Replying to {message.author_username} who replied to our message. "
                                    f"Their message: {message.content}"
                                )
                                gpt_response = await self._gpt_referenced_messages(
                                    message.content,
                                    message.referenced_message_content,
                                )
                                gpt_response = (
                                    gpt_response.replace("```", "")
                                    .replace("```python", "")
                                    .replace("```", "")
                                    .replace('"', "")
                                )
                                random_pause = random.randint(
                                    self.config.AI_CHATTER.PAUSE_BEFORE_MESSAGE[0],
                                    self.config.AI_CHATTER.PAUSE_BEFORE_MESSAGE[1],
                                )
                                logger.info(
                                    f"{self.account.index} | GPT response: {gpt_response}. Pausing for {random_pause} seconds before sending message."
                                )
                                await asyncio.sleep(random_pause)
                                ok, json_response = await self._send_message(
                                    gpt_response,
                                    self.config.AI_CHATTER.CHANNEL_ID,
                                    self.config.AI_CHATTER.GUILD_ID,
                                    message.message_id,
                                )

                                if ok:
                                    logger.success(
                                        f"{self.account.index} | Message with reply to my message sent: {gpt_response}"
                                    )
                                    self.my_account_id = json_response["author"]["id"]
                                    self.my_account_username = json_response["author"][
                                        "username"
                                    ]
                                    # Save the message ID we just replied to
                                    self.my_replies_messages.append(message.message_id)
                                    message_sent, replied_to_me = True, True
                            else:
                                logger.info(
                                    f"{self.account.index} | Skipping reply due to answer_percentage"
                                )

                    if not replied_to_me:
                        # If nobody replied to us or we haven't sent any messages yet,
                        # proceed with normal reply logic
                        replyable_messages = [
                            msg
                            for msg in last_messages
                            if msg.referenced_message_content
                            and msg.author_username
                            != self.my_account_username  # Don't reply to our own messages
                        ]

                        # Determine if we should reply based on percentage and available messages
                        should_reply = (
                            (random.random() * 100)
                            < self.config.AI_CHATTER.REPLY_PERCENTAGE
                            and replyable_messages
                        )

                        if should_reply:
                            # send reply message to someone
                            message = random.choice(replyable_messages)
                            logger.info(
                                f"{self.account.index} | Sending reply message to {message.author_username}. Main message: {message.content}. Referenced message: {message.referenced_message_content}"
                            )
                            gpt_response = await self._gpt_referenced_messages(
                                message.content,
                                message.referenced_message_content,
                            )
                            gpt_response = (
                                gpt_response.replace("```", "")
                                .replace("```python", "")
                                .replace("```", "")
                                .replace('"', "")
                            )

                            random_pause = random.randint(
                                self.config.AI_CHATTER.PAUSE_BEFORE_MESSAGE[0],
                                self.config.AI_CHATTER.PAUSE_BEFORE_MESSAGE[1],
                            )
                            logger.info(
                                f"{self.account.index} | GPT response: {gpt_response}. Pausing for {random_pause} seconds before sending message."
                            )

                            await asyncio.sleep(random_pause)
                            ok, json_response = await self._send_message(
                                gpt_response,
                                self.config.AI_CHATTER.CHANNEL_ID,
                                self.config.AI_CHATTER.GUILD_ID,
                                message.message_id,
                            )

                            if ok:
                                logger.success(
                                    f"{self.account.index} | Message with reply sent: {gpt_response}"
                                )
                                self.my_account_id = json_response["author"]["id"]
                                message_sent = True

                        else:
                            # send simple message based on chat history
                            messages_contents = "| ".join(
                                [message.content for message in last_messages]
                            )
                            # logger.info(
                            #     f"{self.account.index} | Messages contents: {messages_contents}"
                            # )

                            gpt_response = await self._gpt_batch_messages(
                                messages_contents,
                            )
                            gpt_response = (
                                gpt_response.replace("```", "")
                                .replace("```python", "")
                                .replace("```", "")
                                .replace('"', "")
                            )

                            random_pause = random.randint(
                                self.config.AI_CHATTER.PAUSE_BEFORE_MESSAGE[0],
                                self.config.AI_CHATTER.PAUSE_BEFORE_MESSAGE[1],
                            )
                            logger.info(
                                f"{self.account.index} | GPT response: {gpt_response}. Pausing for {random_pause} seconds before sending message."
                            )
                            await asyncio.sleep(random_pause)

                            ok, json_response = await self._send_message(
                                gpt_response,
                                self.config.AI_CHATTER.CHANNEL_ID,
                                self.config.AI_CHATTER.GUILD_ID,
                            )

                            if ok:
                                logger.success(
                                    f"{self.account.index} | Message sent with no reply: {gpt_response}"
                                )
                                self.my_account_id = json_response["author"]["id"]
                                message_sent = True

                    if message_sent:
                        random_pause = random.randint(
                            self.config.AI_CHATTER.PAUSE_BETWEEN_MESSAGES[0],
                            self.config.AI_CHATTER.PAUSE_BETWEEN_MESSAGES[1],
                        )
                        logger.info(
                            f"{self.account.index} | Pausing for {random_pause} seconds before next message."
                        )
                        await asyncio.sleep(random_pause)
                        break

                    else:
                        random_pause = random.randint(
                            self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                            self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
                        )
                        logger.info(
                            f"{self.account.index} | No message send. Pausing for {random_pause} seconds before next try."
                        )
                        await asyncio.sleep(random_pause)

                except Exception as e:
                    logger.error(f"{self.account.index} | Error in start_chatting: {e}")
                    return False

    async def _send_message(
        self,
        message: str,
        channel_id: str,
        guild_id: str,
        reply_to_message_id: str = None,
    ) -> tuple[bool, dict]:
        try:
            headers = {
                "authorization": self.account.token,
                "content-type": "application/json",
                "origin": "https://discord.com",
                "referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
                # 'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InJ1IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMyLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tLyIsInJlZmVycmluZ19kb21haW4iOiJkaXNjb3JkLmNvbSIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozNjY5NTUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImhhc19jbGllbnRfbW9kcyI6ZmFsc2V9',
            }

            json_data = {
                "mobile_network_type": "unknown",
                "content": message,
                "nonce": calculate_nonce(),
                "tts": False,
                "flags": 0,
            }

            if reply_to_message_id:
                json_data["message_reference"] = {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "message_id": reply_to_message_id,
                }

            response = await self.client.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=headers,
                json=json_data,
            )
            if (
                "This action cannot be performed due to slowmode rate limit"
                in response.text
            ):
                logger.info(
                    f"{self.account.index} | Slowmode rate limit. Pausing for 10 seconds."
                )
                await asyncio.sleep(10)

            return response.status_code == 200, response.json()

        except Exception as e:
            logger.error(f"{self.account.index} | Error in send_message: {e}")
            return False, None

    async def _get_last_chat_messages(
        self, guild_id: str, channel_id: str, quantity: int = 50
    ) -> list[str]:
        try:

            headers = {
                "authorization": self.account.token,
                "referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
                # 'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InJ1IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMyLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tLyIsInJlZmVycmluZ19kb21haW4iOiJkaXNjb3JkLmNvbSIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozNjY5NTUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImhhc19jbGllbnRfbW9kcyI6ZmFsc2V9',
            }

            params = {
                "limit": str(quantity),
            }

            response = await self.client.get(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                params=params,
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(
                    f"Error in _get_last_chat_messages: {response.status_code} | {response.text}"
                )
                return []

            received_messages = []
            for message in response.json():
                try:
                    if (
                        "you just advanced to level" in message["content"]
                        or message["content"] == ""
                    ):
                        continue

                    message_data = ReceivedMessage(
                        type=message["type"],
                        content=message["content"],
                        message_id=message["id"],
                        channel_id=message["channel_id"],
                        author_id=message["author"]["id"],
                        author_username=message["author"]["username"],
                        referenced_message_content=(
                            ""
                            if message.get("referenced_message") in ["None", None]
                            else message.get("referenced_message", {}).get(
                                "content", ""
                            )
                        ),
                        referenced_message_author_id=(
                            ""
                            if message.get("referenced_message") in ["None", None]
                            else message.get("referenced_message", {})
                            .get("author", {})
                            .get("id", "")
                        ),
                    )
                    received_messages.append(message_data)
                except Exception as e:
                    continue

            return received_messages

        except Exception as e:
            logger.error(
                f"{self.account.index} | Error in _get_last_chat_messages: {e}"
            )
            return []

    async def _gpt_referenced_messages(
        self, main_message_content: str, referenced_message_content: str
    ) -> str:
        try:
            user_message = f"""Previous message: "{referenced_message_content}"
                Reply to it: "{main_message_content}"
                Generate a natural response continuing this conversation.
            """

            ok, gpt_response = ask_chatgpt(
                random.choice(self.config.CHAT_GPT.API_KEYS),
                self.config.CHAT_GPT.MODEL,
                user_message,
                REFERENCED_MESSAGES_SYSTEM_PROMPT,
                proxy=self.config.CHAT_GPT.PROXY_FOR_CHAT_GPT,
            )

            if not ok:
                raise Exception(gpt_response)

            return gpt_response
        except Exception as e:
            logger.error(
                f"{self.account.index} | Error in chatter _gpt_referenced_messages: {e}"
            )
            raise e

    async def _gpt_batch_messages(self, messages_contents: list[str]) -> str:
        try:
            user_message = f"""
                Chat history: {messages_contents}
            """

            ok, gpt_response = ask_chatgpt(
                random.choice(self.config.CHAT_GPT.API_KEYS),
                self.config.CHAT_GPT.MODEL,
                user_message,
                BATCH_MESSAGES_SYSTEM_PROMPT,
                proxy=self.config.CHAT_GPT.PROXY_FOR_CHAT_GPT,
            )

            if not ok:
                raise Exception(gpt_response)

            return gpt_response
        except Exception as e:
            logger.error(
                f"{self.account.index} | Error in chatter _gpt_batch_messages: {e}"
            )
            raise e
