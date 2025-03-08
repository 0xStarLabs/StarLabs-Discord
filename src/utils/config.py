from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import yaml
from pathlib import Path
import asyncio

from src.utils.constants import DataForTasks


@dataclass
class SettingsConfig:
    DISCORD_TOKEN_FOR_PARSING: str
    PROXY_FOR_PARSING: str
    THREADS: int
    ATTEMPTS: int
    SHUFFLE_ACCOUNTS: bool
    ACCOUNTS_RANGE: Tuple[int, int]
    EXACT_ACCOUNTS_TO_USE: List[int]
    PAUSE_BETWEEN_ATTEMPTS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACCOUNTS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACTIONS: Tuple[int, int]
    RANDOM_INITIALIZATION_PAUSE: Tuple[int, int]
    RANDOM_PROFILE_PICTURES: bool

    TASK: str
    DATA_FOR_TASKS: DataForTasks

@dataclass
class ChatterConfig:
    GUILD_ID: str
    CHANNEL_ID: str
    ANSWER_PERCENTAGE: int
    REPLY_PERCENTAGE: int
    MESSAGES_TO_SEND_PER_ACCOUNT: Tuple[int, int]
    PAUSE_BETWEEN_MESSAGES: Tuple[int, int]
    PAUSE_BEFORE_MESSAGE: Tuple[int, int]

@dataclass
class MessageSenderConfig:
    GUILD_ID: str
    CHANNEL_ID: str
    DELETE_MESSAGE_INSTANTLY: bool
    SEND_MESSAGES_RANDOMLY: bool
    NUMBER_OF_MESSAGES_TO_SEND: int
    PAUSE_BETWEEN_MESSAGES: Tuple[int, int]

@dataclass
class ChatGPTConfig:
    API_KEYS: List[str]
    MODEL: str
    PROXY_FOR_CHAT_GPT: str

@dataclass
class Config:
    SETTINGS: SettingsConfig
    AI_CHATTER: ChatterConfig
    CHAT_GPT: ChatGPTConfig
    MESSAGE_SENDER: MessageSenderConfig
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        """Load configuration from yaml file"""
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        return cls(
            SETTINGS=SettingsConfig(
                DISCORD_TOKEN_FOR_PARSING=data["SETTINGS"]["DISCORD_TOKEN_FOR_PARSING"],
                PROXY_FOR_PARSING=data["SETTINGS"]["PROXY_FOR_PARSING"],
                THREADS=data["SETTINGS"]["THREADS"],
                ATTEMPTS=data["SETTINGS"]["ATTEMPTS"],
                SHUFFLE_ACCOUNTS=data["SETTINGS"]["SHUFFLE_ACCOUNTS"],
                ACCOUNTS_RANGE=tuple(data["SETTINGS"]["ACCOUNTS_RANGE"]),
                EXACT_ACCOUNTS_TO_USE=data["SETTINGS"]["EXACT_ACCOUNTS_TO_USE"],
                PAUSE_BETWEEN_ATTEMPTS=tuple(
                    data["SETTINGS"]["PAUSE_BETWEEN_ATTEMPTS"]
                ),
                RANDOM_PAUSE_BETWEEN_ACCOUNTS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACCOUNTS"]
                ),
                RANDOM_PAUSE_BETWEEN_ACTIONS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACTIONS"]
                ),
                RANDOM_INITIALIZATION_PAUSE=tuple(
                    data["SETTINGS"]["RANDOM_INITIALIZATION_PAUSE"]
                ),
                RANDOM_PROFILE_PICTURES=data["SETTINGS"]["RANDOM_PROFILE_PICTURES"],
                TASK="",
                DATA_FOR_TASKS=None,
            ),
            AI_CHATTER=ChatterConfig(
                GUILD_ID=data["AI_CHATTER"]["GUILD_ID"],
                CHANNEL_ID=data["AI_CHATTER"]["CHANNEL_ID"],
                ANSWER_PERCENTAGE=data["AI_CHATTER"]["ANSWER_PERCENTAGE"],
                REPLY_PERCENTAGE=data["AI_CHATTER"]["REPLY_PERCENTAGE"],
                MESSAGES_TO_SEND_PER_ACCOUNT=tuple(
                    data["AI_CHATTER"]["MESSAGES_TO_SEND_PER_ACCOUNT"]
                ),
                PAUSE_BETWEEN_MESSAGES=tuple(data["AI_CHATTER"]["PAUSE_BETWEEN_MESSAGES"]),
                PAUSE_BEFORE_MESSAGE=tuple(data["AI_CHATTER"]["PAUSE_BEFORE_MESSAGE"]),
            ),
            MESSAGE_SENDER=MessageSenderConfig(
                GUILD_ID=data["MESSAGE_SENDER"]["GUILD_ID"],
                CHANNEL_ID=data["MESSAGE_SENDER"]["CHANNEL_ID"],
                DELETE_MESSAGE_INSTANTLY=data["MESSAGE_SENDER"]["DELETE_MESSAGE_INSTANTLY"],
                SEND_MESSAGES_RANDOMLY=data["MESSAGE_SENDER"]["SEND_MESSAGES_RANDOMLY"],
                NUMBER_OF_MESSAGES_TO_SEND=data["MESSAGE_SENDER"]["NUMBER_OF_MESSAGES_TO_SEND"],
                PAUSE_BETWEEN_MESSAGES=tuple(data["MESSAGE_SENDER"]["PAUSE_BETWEEN_MESSAGES"]),
            ),
            CHAT_GPT=ChatGPTConfig(
                API_KEYS=data["CHAT_GPT"]["API_KEYS"],
                MODEL=data["CHAT_GPT"]["MODEL"],
                PROXY_FOR_CHAT_GPT=data["CHAT_GPT"]["PROXY_FOR_CHAT_GPT"],
            ),
        )


# Singleton pattern
def get_config() -> Config:
    """Get configuration singleton"""
    if not hasattr(get_config, "_config"):
        get_config._config = Config.load()
    return get_config._config
