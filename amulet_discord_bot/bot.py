import discord
import argparse
import re
import gzip
import os
from difflib import SequenceMatcher

from amulet_discord_bot.const import Servers, Chats, HelpMessages, QuestionMessages

github_match = re.compile(r"https?://(www.)?github.com/.*/.*")
url_match = re.compile(
    r"https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)"
)

with gzip.open(os.path.join(os.path.dirname(__file__), "prof"), "rb") as f:
    prof_match = re.compile(
        f.read().decode("utf-8"), flags=re.IGNORECASE | re.MULTILINE
    )


class AmuletBot(discord.Client):
    async def _log(self, msg: str):
        chat = self.get_channel(Chats.ServerLog)
        await chat.send(msg)

    async def on_ready(self):
        await self._log("I am back")

    async def ban(self, member: discord.Member, reason: str = None):
        """Ban a user from the server"""
        if isinstance(member, discord.Member) and len(member.roles) == 1:
            await self._log(f"{member} is banned! reason={reason}")
            reason = (
                f"{reason}\n"
                f"If you think this was done in error please contact a moderator.\n\n"
            )
            server: discord.Guild = self.get_guild(Servers.AmuletServer)
            await server.ban(member, reason=reason)

    async def _remove_and_dm(self, message, dm_str):
        """Remove a given message and let the user know."""
        fmt_msg = message.content.replace("```", r"`\``")
        if fmt_msg == message.content:
            extra_msg = ""
        else:
            extra_msg = " You will need to fix the triple backticks."
        await self._log(
            f"Messaged removed from {message.author.name} in {message.channel.name}\n"
            f"```\n{fmt_msg}\n```"
        )
        try:
            await message.author.send(
                f"{dm_str}\n"
                f"If you think this was done in error please contact a moderator.\n\n"
                f"The message you sent is as follows.{extra_msg}\n"
                f"```\n{fmt_msg}\n```"
            )
        except:
            pass
        await message.delete()

    @staticmethod
    def has_link(msg: str) -> bool:
        """Returns true if the message contains what looks like a link."""
        return url_match.search(msg) is not None

    @staticmethod
    def has_github_link(msg: str) -> bool:
        """Returns true if the message contains a github link."""
        return github_match.search(msg) is not None

    async def on_message(self, message: discord.Message):
        author = message.author
        author_id = author.id
        if author_id == self.user.id:
            return
        channel_id = message.channel.id
        message_text = message.content
        if channel_id == Chats.AmuletPlugins:
            if not self.has_github_link(message_text):
                await self._remove_and_dm(
                    message,
                    "Hello. You just sent a message to the amulet-plugins chat.\n"
                    "This chat is reserved for users to show off plugins they have created.\n"
                    "Messages must include a link to the plugin on github.\n",
                )
                return
        elif channel_id == Chats.AmuletGeneral and len(message_text) < 30:
            for msg in HelpMessages:
                if SequenceMatcher(None, message_text, msg).ratio() > 0.5:
                    await message.reply(
                        "Hello it looks like you want some help. "
                        "What is the problem and how can we help you?"
                    )
                    return
            for msg in QuestionMessages:
                if SequenceMatcher(None, message_text, msg).ratio() > 0.5:
                    await message.reply(
                        "Hello it looks like you want to ask a question. "
                        "This is the place to do that. "
                        "Write your question and someone will respond when they are available."
                    )
                    return
        elif channel_id == Chats.ServerLog and message_text == "!ping":
            await self._log("Pong!")
            return

        if prof_match.search(message_text) is not None:
            await self._remove_and_dm(
                message,
                "Hello. We believe your message contains profanity so it was automatically removed.\n"
                "Please remove the profanity before sending it again.",
            )
            return
        if self.has_link(message_text) and not self.has_github_link(message_text):
            server: discord.Guild = self.get_guild(Servers.AmuletServer)
            count = 1
            for channel in server.text_channels:
                if (
                    channel.id != channel_id
                    and channel.permissions_for(author).read_message_history
                ):
                    async for message_ in channel.history(limit=30):
                        message_: discord.Message
                        if (
                            message_.author.id == author_id
                            and SequenceMatcher(
                                None, message_text, message_.content
                            ).ratio()
                            > 0.9
                        ):
                            count += 1
                            break
                if count >= 3:
                    break
            if count >= 3:
                await self.ban(author, f"spamming\n{message_text}")
            return


def main():
    parser = argparse.ArgumentParser(description="Run the Amulet Discord bot.")
    parser.add_argument("bot_token", type=str)
    args = parser.parse_args()

    client = AmuletBot()
    client.run(args.bot_token)
