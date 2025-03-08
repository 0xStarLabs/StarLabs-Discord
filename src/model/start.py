from loguru import logger
from curl_cffi.requests import AsyncSession
import random
import asyncio

from src.model.discord.button_presser import press_button
from src.model.discord.inviter import Inviter
from src.model.discord import message_sender
from src.model.discord import token_checker
from src.model.discord import get_all_servers, check_if_token_in_guild
from src.model.discord import leave_guild
from src.model.discord.chatter import DiscordChatter
from src.model.discord.account_editor import AccountEditor
from src.utils.client import create_client
from src.utils.config import Config
from src.utils.constants import Account
from src.model.discord.reaction_presser import reaction_presser

class Start:
    def __init__(
        self,
        account: Account,
        config: Config,
    ):
        self.account = account
        self.config = config

        self.session: AsyncSession | None = None

    async def initialize(self):
        try:
            self.session = await create_client(self.account.proxy)

            return True
        except Exception as e:
            logger.error(f"[{self.account.index}] | Error: {e}")
            return False

    async def flow(self):
        try:
            if self.config.TASK == "Inviter [Token]":
                inviter = Inviter(self.account, self.config, self.session)
                await inviter.invite(self.config.DATA_FOR_TASKS.INVITE_CODE)

            if self.config.TASK == "AI Chatter":
                chatter = DiscordChatter(self.account, self.session, self.config)
                await chatter.start_chatting()

            if self.config.TASK == "Press Button [Token]":
                button = await press_button(self.account, self.config, self.session)

            if self.config.TASK == "Press Reaction [Token]":
                reaction = await reaction_presser(self.account, self.config, self.session)

            if self.config.TASK == "Leave Guild [Token]":
                for guild_id in self.config.DATA_FOR_TASKS.LEAVE_GUILD_IDS:
                    await leave_guild(self.account, self.config, guild_id)

            if self.config.TASK == "Show all servers account is in [Token]":
                await get_all_servers(self.account, self.config, self.session)

            if self.config.TASK == "Token Checker [Token]":
                await token_checker(self.account, self.config, self.session)

            if "Change" in self.config.TASK:
                editor = AccountEditor(self.account, self.config, self.session)
                if self.config.TASK == "Change Name [Token]":
                    await editor.change_name()
                if self.config.TASK == "Change Username [Token + Password]":
                    await editor.change_username()
                if self.config.TASK == "Change Password [Token + Password]":
                    await editor.change_password()
                if self.config.TASK == "Change Profile Picture [Token]":
                    await editor.change_profile_picture()

            if self.config.TASK == "Send message to the channel [Token]":
                await message_sender(self.account, self.config, self.session)

            if self.config.TASK == "Check if token in specified Guild [Token]":
                await check_if_token_in_guild(self.account, self.config, self.session)
                
            await self.sleep(self.config.TASK)

            return True
        except Exception as e:
            logger.error(f"[{self.account.index}] | Error: {e}")
            return False

    async def sleep(self, task_name: str):
        """Делает рандомную паузу между действиями"""
        pause = random.randint(
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
        )
        logger.info(
            f"[{self.account.index}] Sleeping {pause} seconds after {task_name}"
        )
        await asyncio.sleep(pause)
