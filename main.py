from loguru import logger
import urllib3
import sys
import asyncio

from process import start


async def main():
    configuration()
    await start()


def configuration():
    urllib3.disable_warnings()
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<light-cyan>{time:HH:mm:ss}</light-cyan> | <level>{level: <8}</level> | <fg #ffffff>{name}:{line}</fg #ffffff> - <bold>{message}</bold>",
    )


if __name__ == "__main__":
    asyncio.run(main())