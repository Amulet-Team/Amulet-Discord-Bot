import traceback
import argparse
import re
import gzip
import os
from difflib import SequenceMatcher

import discord

from .const import Servers, Chats, HelpMessages, QuestionMessages, SURoles, Roles

GithubURLPattern = re.compile(r"https?://(www.)?github.com/.*/.*")
URLPattern = re.compile(
    r"https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)"
)
UserPattern = re.compile("<@(?P<user_id>[0-9]+)>")

with gzip.open(os.path.join(os.path.dirname(__file__), "prof"), "rb") as f:
    prof_match = re.compile(
        f.read().decode("utf-8"), flags=re.IGNORECASE | re.MULTILINE
    )


class AmuletBot(discord.Client):
    async def _log(self, msg: str) -> None:
        chat = self.get_channel(Chats.ServerLog)
        if isinstance(chat, discord.abc.Messageable):
            await chat.send(msg)

    async def on_ready(self) -> None:
        try:
            await self._log(f"I am {os.getlogin()} and I am back")
        except:
            await self._log("I am back")

    async def ban(self, member: discord.Member, reason: str = "Undefined") -> None:
        """Ban a user from the server"""
        if isinstance(member, discord.Member) and not self._is_super_user(member):
            await self._log(f"{member} is banned! reason={reason}")
            reason = (
                f"{reason}\n"
                f"If you think this was done in error please contact a moderator.\n\n"
            )
            server = self.get_guild(Servers.AmuletServer)
            if server is not None:
                await server.ban(member, reason=reason)

    async def _remove_and_dm(self, message: discord.Message, dm_str: str) -> None:
        """Remove a given message and let the user know."""
        fmt_msg = message.content.replace("```", r"`\``")
        if fmt_msg == message.content:
            extra_msg = ""
        else:
            extra_msg = " You will need to fix the triple backticks."
        dm_message = (
            f"{dm_str}\n"
            f"If you think this was done in error please contact a moderator.\n\n"
            f"The message you sent is as follows.{extra_msg}\n"
            f"```\n{fmt_msg}\n```"
        )
        author = message.author
        channel = message.channel
        channel_name = getattr(channel, "name", "Unknown channel")
        await self._log(
            f"Message removed from {author.name} in {channel_name}. The warning sent to the user is as follows.\n"
            f"{dm_message}"
        )
        try:
            await author.send(dm_message)
        except:
            pass
        await message.delete()

    @staticmethod
    def has_link(msg: str) -> bool:
        """Returns true if the message contains what looks like a link."""
        return URLPattern.search(msg) is not None

    @staticmethod
    def has_github_link(msg: str) -> bool:
        """Returns true if the message contains a github link."""
        return GithubURLPattern.search(msg) is not None

    def _is_super_user(
        self, author: discord.Member, amulet_server: discord.Guild | None = None
    ) -> bool:
        if amulet_server is None:
            amulet_server = self.get_guild(Servers.AmuletServer)
            if amulet_server is None:
                return False
        super_user_roles = [amulet_server.get_role(role_id) for role_id in SURoles]
        for role in super_user_roles:
            if role in author.roles:
                return True
        return False

    def _get_own_id(self) -> int | None:
        user = self.user
        if user is None:
            return None
        else:
            return user.id

    async def _process_message(self, message: discord.Message) -> None:
        amulet_server = self.get_guild(Servers.AmuletServer)
        author = message.author
        if not isinstance(author, discord.Member):
            return
        author_id = author.id
        if author_id == self._get_own_id():
            return
        channel_id = message.channel.id
        message_text = message.content

        if prof_match.search(message_text) is not None:
            # check for profanity
            await self._remove_and_dm(
                message,
                "Hello. We believe your message contains profanity so it was automatically removed.\n"
                "Please remove the profanity before sending it again.",
            )
            return

        if amulet_server is not None and not self._is_super_user(author, amulet_server):
            # if sender is not a super-user and they @someone with the DoNotAtMe role, remove the message.
            do_not_at_me_role: discord.Role | None = None

            for match in UserPattern.finditer(message_text):
                user_id = int(match.group("user_id"))
                if user_id == author_id:
                    # if they @themselves
                    continue
                if do_not_at_me_role is None:
                    do_not_at_me_role = amulet_server.get_role(Roles.DoNotAtMe)
                    if do_not_at_me_role is None:
                        # could not find the role
                        break
                user = amulet_server.get_member(user_id)
                if user is None:
                    continue
                if do_not_at_me_role in user.roles:
                    await self._remove_and_dm(
                        message,
                        "Please do not tag users. If you have a question please read the FAQ and search the discord to see if your question has already been asked.",
                    )
                    return

        if channel_id == Chats.AmuletPlugins:
            # enforce links in the plugin chat having a github link
            if not self.has_github_link(message_text):
                await self._remove_and_dm(
                    message,
                    "Hello. You just sent a message to the amulet-plugins chat.\n"
                    "This chat is reserved for users to show off plugins they have created.\n"
                    "Messages must include a link to the plugin on github.\n",
                )
                return

        elif channel_id == Chats.AmuletGeneral and len(message_text) < 30:
            # respond to help like messages
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
            # alive check
            try:
                await self._log(f"Pong! {os.getlogin()}")
            except:
                await self._log(f"Pong!")
            return

        if (
            amulet_server is not None
            and self.has_link(message_text)
            and not self.has_github_link(message_text)
        ):
            # remove spam messages
            count = 1
            for channel in amulet_server.text_channels:
                if (
                    channel.id != channel_id
                    and channel.permissions_for(author).read_message_history
                ):
                    async for other_message in channel.history(limit=30):
                        other_author = other_message.author
                        if (
                            other_author.id == author_id
                            and SequenceMatcher(
                                None, message_text, other_message.content
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

    async def on_message(self, message: discord.Message) -> None:
        try:
            await self._process_message(message)
        except Exception:
            await self._log(traceback.format_exc())
            traceback.print_exc()

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        try:
            server = self.get_guild(Servers.AmuletServer)
            if server is None:
                return
            channel = server.get_channel(payload.channel_id)
            if not isinstance(channel, discord.abc.Messageable):
                return
            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.Forbidden:
                pass
            else:
                await self._process_message(message)
        except Exception:
            await self._log(traceback.format_exc())
            traceback.print_exc()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Amulet Discord bot.")
    parser.add_argument("bot_token", type=str)
    args = parser.parse_args()

    intents = discord.Intents.default()
    intents.members = True
    client = AmuletBot(intents=intents)
    client.run(args.bot_token)
