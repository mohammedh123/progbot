import asyncio
import logging
import os
import signal

import discord
from admin import Admin
from discord.ext import commands
from prog_analyzer import ProgAnalyzer

logger = logging.getLogger(__name__)


async def main() -> None:
    signal.signal(signal.SIGINT, lambda _, __: asyncio.create_task(os._exit(0)))
    discord.utils.setup_logging(level=logging.INFO)
    logging.getLogger("discord").setLevel(logging.WARNING)

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    await bot.add_cog(Admin(bot))
    await bot.add_cog(
        ProgAnalyzer(
            bot,
            os.getenv("FFLOGS_API_CLIENT_ID"),
            os.getenv("FFLOGS_API_CLIENT_SECRET"),
        )
    )
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
