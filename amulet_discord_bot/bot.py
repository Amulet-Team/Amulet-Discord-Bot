import discord
import argparse
import re
from difflib import SequenceMatcher

from amulet_discord_bot.const import Chats, HelpMessages, QuestionMessages

github_match = re.compile(r"https?://(www.)?github.com/.*/.*")


class AmuletBot(discord.Client):
    async def _log(self, msg: str):
        chat = self.get_channel(Chats.ServerLog)
        await chat.send(msg)

    async def on_ready(self):
        await self._log("I am back")

    async def on_message(self, message):
        if message.channel.id == Chats.AmuletPlugins:
            if github_match.search(message.content) is None:
                fmt_msg = message.content.replace("```", r"`\``")
                if fmt_msg == message.content:
                    extra_msg = ""
                else:
                    extra_msg = " You will need to fix the triple backticks."
                await message.author.send(
                    f"Hello. You just sent a message to the amulet-plugins chat.\n"
                    f"This chat is reserved for users to show off plugins they have created.\n"
                    f"Messages must include a link to the plugin on github.\n"
                    f"If you think this was done in error please contact a moderator.\n\n"
                    f"The message you sent is as follows.{extra_msg}\n"
                    f"```\n{fmt_msg}\n```"
                )
                await message.delete()
                return
        elif message.channel.id == Chats.AmuletGeneral and len(message.content) < 30:
            for msg in HelpMessages:
                if SequenceMatcher(None, message.content, msg).ratio() > 0.5:
                    await message.reply(
                        "Hello it looks like you want some help. "
                        "What is the problem and how can we help you?"
                    )
                    return
            for msg in QuestionMessages:
                if SequenceMatcher(None, message.content, msg).ratio() > 0.5:
                    await message.reply(
                        "Hello it looks like you want to ask a question. "
                        "This is the place to do that. "
                        "Write your question and someone will respond when they are available."
                    )
                    return


def main():
    parser = argparse.ArgumentParser(description="Run the Amulet Discord bot.")
    parser.add_argument("bot_token", type=str)
    args = parser.parse_args()

    client = AmuletBot()
    client.run(args.bot_token)
