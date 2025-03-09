import base64
import json
import os
import yaml
import threading
from loguru import logger
from openpyxl import load_workbook
from typing import List, Dict
from src.utils.constants import Account

# Создаем глобальный lock для синхронизации доступа к файлам
file_read_lock = threading.Lock()


def read_txt_file(file_name: str, file_path: str) -> list:
    """
    Безопасно считывает текстовый файл с использованием блокировки

    Args:
        file_name: Имя файла для логирования
        file_path: Полный путь к файлу

    Returns:
        Список строк из файла или пустой список, если файл не существует
    """
    with file_read_lock:
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                logger.warning(f"File {file_path} does not exist.")
                return []

            # Читаем файл
            with open(file_path, "r", encoding="utf-8") as file:
                items = [line.strip() for line in file if line.strip()]

            if not items:
                logger.warning(f"File {file_path} is empty.")
                return []

            logger.success(f"Successfully loaded {len(items)} items from {file_name}.")
            return items

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return []


def read_xlsx_accounts(file_path: str) -> List[Account]:
    """
    Читает данные аккаунтов из XLSX файла.
    Читает до первой пустой строки в колонке DISCORD_TOKEN.

    Args:
        file_path (str): Путь к XLSX файлу

    Returns:
        List[Account]: Список объектов Account с данными аккаунтов
    """
    workbook = load_workbook(filename=file_path, read_only=True)
    sheet = workbook.active
    accounts = []

    # Начинаем со второй строки (пропускаем заголовки)
    for row_index, row in enumerate(list(sheet.rows)[1:], 1):
        # Получаем значение токена (первая колонка)
        token = str(row[0].value or "")

        # Если токен пустой - прерываем чтение
        if not token.strip():
            break

        # Получаем остальные значения, заменяя None на пустую строку
        proxy = str(row[1].value or "")
        username = str(row[2].value or "")
        status = str(row[3].value or "")
        password = str(row[4].value or "")
        new_password = str(row[5].value or "")
        new_name = str(row[6].value or "")
        new_username = str(row[7].value or "")
        messages_txt_name = str(row[8].value or "")

        messages_to_send = []
        if messages_txt_name.strip():
            messages_to_send = read_txt_file(
                messages_txt_name, f"data/messages/{messages_txt_name}.txt"
            )

        account = Account(
            index=row_index,
            token=token.strip(),
            proxy=proxy.strip(),
            username=username.strip(),
            status=status.strip(),
            password=password.strip(),
            new_password=new_password.strip(),
            new_name=new_name.strip(),
            new_username=new_username.strip(),
            messages_to_send=messages_to_send,
        )
        accounts.append(account)

    logger.success(
        f"Successfully loaded {len(accounts)} accounts from data/accounts.xlsx"
    )
    workbook.close()
    return accounts


async def read_pictures(file_path: str) -> List[str]:
    """
    Считывает изображения из указанной папки и кодирует их в base64

    Args:
        file_path: Путь к папке с изображениями

    Returns:
        Список закодированных изображений в формате base64
    """
    encoded_images = []

    # Создаем папку, если она не существует
    os.makedirs(file_path, exist_ok=True)
    logger.info(f"Reading pictures from {file_path}")

    try:
        # Получаем список файлов
        files = os.listdir(file_path)

        if not files:
            logger.warning(f"No files found in {file_path}")
            return encoded_images

        # Обрабатываем каждый файл
        for filename in files:
            if filename.endswith((".png", ".jpg", ".jpeg")):
                # Формируем полный путь к файлу
                image_path = os.path.join(file_path, filename)

                try:
                    with open(image_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode(
                            "utf-8"
                        )
                        encoded_images.append(encoded_image)
                except Exception as e:
                    logger.error(f"Error loading image {filename}: {str(e)}")

    except FileNotFoundError:
        logger.error(f"Directory not found: {file_path}")
    except PermissionError:
        logger.error(f"Permission denied when accessing: {file_path}")
    except Exception as e:
        logger.error(f"Error reading pictures from {file_path}: {str(e)}")

    return encoded_images
