"""Obsidian Bot Configuration"""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = '!'
OWNER_ID = 1178422093549936686
GUILD_ID = 1272576387701805136

WELCOME_CHANNEL = 1272576389513609293
RULES_CHANNEL = 1519547820644765778
ANNOUNCEMENT_CHANNEL = 1519548052300501197
TICKET_LOG_CHANNEL = 1272576392994754665
MOD_LOG_CHANNEL = 1272576392994754667
MESSAGE_LOG_CHANNEL = 1272576392994754669
VOUCH_CHANNEL = 1272576391417827426

STAFF_ROLE = 1272576388183887979
ADMIN_ROLE = 1272576388183887981
MOD_ROLE = 1272576388183887980
VERIFIED_ROLE = 1272576387919904827
MUTED_ROLE = 0

TICKET_CATEGORY = 1272576393326231604
TICKET_STAFF_ROLE = 1272576388183887980

SPAM_THRESHOLD = 5
SPAM_INTERVAL = 5
MENTION_LIMIT = 5
MIN_ACCOUNT_AGE = 7

SCAM_KEYWORDS = [
    'free robux', 'free nitro', 'nitro gen', 'stealer', 'grabber',
    'token logger', 'discord.gg/free', 'gift-nitro', 'robux generator',
    'free items', 'click here for free', 'get free', 'd1scord',
    'disc0rd', 'r0bux', 'steamcommunity.com/gift'
]

SUSPICIOUS_KEYWORDS = [
    'check my bio', 'check my profile', 'first link in bio',
    'dm for trade', 'cheap robux', '50% off robux', 'double your robux'
]

STARTING_BALANCE = 0
DAILY_REWARD = 100
BOOSTER_BONUS = 50

EMBED_COLOR = 0x2B2D31
SUCCESS_COLOR = 0x57F287
ERROR_COLOR = 0xED4245
WARNING_COLOR = 0xFEE75C
INFO_COLOR = 0x5865F2
TICKET_COLOR = 0xEB459E
SHOP_COLOR = 0xEB459E

PRICE_TIERS = {
    '1k-4k': {'emoji': '🥉', 'min': 1000, 'max': 4000},
    '5k-10k': {'emoji': '🥈', 'min': 5000, 'max': 10000},
    '11k-15k': {'emoji': '🥇', 'min': 11000, 'max': 15000}
}

MODEL_CATEGORIES = [
    'vegetation-models', 'chinese-theme-models', 'car-models', 'rocket-models'
]

WELCOME_MESSAGE = """
Welcome to **Obsidian Marketplace**, {user}! 🖤

➜ Read <#{rules}> before doing anything
➜ Verify yourself in the verification channel
➜ Browse assets by price tier
➜ Open a ticket for purchases or support

🔒 All sales are protected — scammers will be banned.
"""
