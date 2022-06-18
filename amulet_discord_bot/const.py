from enum import IntEnum


class Servers(IntEnum):
    AmuletServer = 324647192583340043


class Chats(IntEnum):
    AmuletGeneral = 498974201416253443
    AmuletPlugins = 856261919689932840
    ServerLog = 884022949756153906


class Roles(IntEnum):
    Admin = 856554538777837609
    Moderator = 400880673939914762
    CommunityManager = 851887458462334997
    AmuletDeveloper = 582683220760592385
    DoNotAtMe = 986540956671180820


SURoles = [Roles.Admin, Roles.Moderator, Roles.CommunityManager, Roles.AmuletDeveloper]

HelpMessages = ["help", "help me", "can someone help me"]

QuestionMessages = ["can I ask a question"]
