import asyncio
from src.utils.constants import DataForTasks
from src.utils.config import Config
from src.utils.reader import read_pictures
from loguru import logger

from src.utils.client import create_client


async def prepare_data(config: Config, task: str) -> DataForTasks:
    data = DataForTasks(
        LEAVE_GUILD_IDS=[],
        PROFILE_PICTURES=[],
        EMOJIS_INFO=[],
        INVITE_CODE=None,
        REACTION_CHANNEL_ID=None,
        REACTION_MESSAGE_ID=None,
        IF_TOKEN_IN_GUILD_ID=None,
        BUTTON_PRESSER_BUTTON_DATA=None,
        BUTTON_PRESSER_APPLICATION_ID=None,
        BUTTON_PRESSER_GUILD_ID=None,
        BUTTON_PRESSER_CHANNEL_ID=None,
        BUTTON_PRESSER_MESSAGE_ID=None,
    )

    if task == "Press Button [Token]":
        message_link = input("Paste the link to the message for button presser task: ").strip()
        guild_id = message_link.split("/")[-3]
        channel_id = message_link.split("/")[-2]
        message_id = message_link.split("/")[-1]

        button_data, application_id = await message_click_button_info(channel_id, message_id, config)
        if button_data is None:
            raise Exception("Failed to get button data")
        
        data.BUTTON_PRESSER_BUTTON_DATA = button_data
        data.BUTTON_PRESSER_APPLICATION_ID = application_id
        data.BUTTON_PRESSER_GUILD_ID = guild_id
        data.BUTTON_PRESSER_CHANNEL_ID = channel_id
        data.BUTTON_PRESSER_MESSAGE_ID = message_id

    if task == "Leave Guild [Token]":
        # Разбиваем по запятым или пробелам и фильтруем пустые строки
        guild_ids = input(" > Enter guild ids (comma or space separated): ")
        data.LEAVE_GUILD_IDS = [
            guild_id.strip()
            for guild_id in guild_ids.replace(",", " ").split()
            if guild_id.strip()
        ]

    if task == "Change Profile Picture [Token]":
        # Используем константный путь к папке с картинками
        pictures_path = "data/pictures"
        data.PROFILE_PICTURES = await read_pictures(pictures_path)
        logger.info(
            f"Loaded {len(data.PROFILE_PICTURES)} profile pictures from {pictures_path}"
        )

    if task == "Inviter [Token]":
        invite_code = input(" > Enter invite code: ").strip()
        data.INVITE_CODE = invite_code

    if task == "Press Reaction [Token]":
        message_link = input(
            "Paste the link to the message (for reaction presser task): "
        ).strip()
        channel_id = message_link.split("/")[-2]
        message_id = message_link.split("/")[-1]
        data.REACTION_CHANNEL_ID = channel_id
        data.REACTION_MESSAGE_ID = message_id

        emojis_info = await message_reactions_emojis_info(
            channel_id, message_id, config
        )
        if not emojis_info:
            return
        data.EMOJIS_INFO = emojis_info

    if task == "Check if token in specified Guild [Token]":
        guild_id = input(" > Enter guild id: ").strip()
        data.IF_TOKEN_IN_GUILD_ID = guild_id

    return data


async def message_reactions_emojis_info(
    channel_id: str, message_id: str, config: Config
) -> list | None:
    try:
        emojis = None
        for _ in range(config.SETTINGS.ATTEMPTS):
            session = await create_client(config.SETTINGS.PROXY_FOR_PARSING)

            resp = await session.get(
                f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=1&around={message_id}",
                headers={"Authorization": config.SETTINGS.DISCORD_TOKEN_FOR_PARSING},
            )

            if "reactions" not in resp.text:
                logger.warning(f"There are no reactions on this message.")
                await asyncio.sleep(2)
            else:
                emojis = resp.json()[0]["reactions"]
                break

        if emojis is None:
            logger.error(f"Failed to get emojis info.")
            return None

        emoji_data = {}
        emoji_list_to_show = []

        for emoji in emojis:
            emoji_data[emoji["emoji"]["name"]] = {
                "name": emoji["emoji"]["name"],
                "count": emoji["count"],
                "id": emoji["emoji"]["id"],
            }
            emoji_list_to_show.append(
                f"{emoji['emoji']['name']} | Count: {emoji['count']}"
            )

        for index, emoji in enumerate(emoji_list_to_show, 1):
            print(f"{index} | {emoji}")

        user_choice = input("Choose the emoji: ").split()
        selected_emojis = []

        for choice in user_choice:
            index = int(choice) - 1  # Convert to 0-based index
            emoji_info = emojis[index]["emoji"]  # Get original emoji info
            selected_emojis.append(
                {
                    "name": emoji_info["name"],
                    "id": emoji_info["id"],
                    "count": emojis[index]["count"],
                }
            )

        return selected_emojis

    except Exception as err:
        logger.error(f"Failed to get emojis info: {err}")
        return None


async def message_click_button_info(channel_id: str, message_id: str, config: Config) -> tuple[dict, str] | None:
    try:
        session = await create_client(config.SETTINGS.PROXY_FOR_PARSING)

        resp = await session.get(
            f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=1&around={message_id}",
            headers={"Authorization": config.SETTINGS.DISCORD_TOKEN_FOR_PARSING},
        )

        if '"custom_id":"enter-giveaway"' in resp.text:
            return resp.json()[0]['components'][0]['components'][0], resp.json()[0]['author']['id'], True

        result = choose_button_to_click(resp.json()[0]['components'])

        return result, resp.json()[0]['author']['id']

    except Exception as err:
        logger.error(f'Failed to get message info: {err}')
        return None, None
    

def choose_button_to_click(components: list) -> dict | None:
    try:
        def collect_components(element):
            parsed_components = []
            if isinstance(element, dict):
                if element.get("type") == 2:
                    parsed_components.append(element)
                for key, value in element.items():
                    parsed_components.extend(collect_components(value))
            elif isinstance(element, list):
                for item in element:
                    parsed_components.extend(collect_components(item))

            return parsed_components

        all_components = collect_components(components)

        buttons = []
        for index, comp in enumerate(all_components, start=1):
            buttons.append(comp['label'])

        print("\nButtons:")
        for index, button in enumerate(buttons, start=1):
            print(f"  [{index}] | {button}")

        user_choice = input("\nChoose the button: ").split()
        selected_button = buttons[int(user_choice[0]) - 1]

        for index, comp in enumerate(all_components, start=1):
            if comp['label'] == selected_button:
                return comp

    except Exception as err:
        logger.error(f"Failed to choose button to click: {err}")
        return None