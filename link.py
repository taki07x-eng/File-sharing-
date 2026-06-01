import asyncio
import logging
import re
import aiohttp
import uuid
import html
import json
import time
import os
import tempfile
import pytz
import urllib.parse
from datetime import datetime, timedelta
from typing import Union, List, Optional, Dict, Any
from dotenv import load_dotenv
load_dotenv()

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, idle, filters, enums
from pyrogram.errors import (
    FloodWait, 
    UserNotParticipant, 
    ChatAdminRequired, 
    InviteHashExpired, 
    InviteHashInvalid,
    MessageNotModified,
    RPCError
)
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    ChatPrivileges
)
from pyrogram.handlers import MessageHandler, ChatMemberUpdatedHandler
from pyrogram import ContinuePropagation
from pymongo import MongoClient

send_semaphore = asyncio.Semaphore(5)

# --- GLOBAL SESSION FOR INSTANT GENERATION ---
http_session = None

async def get_session():
    global http_session
    if http_session is None or http_session.closed:
        connector = aiohttp.TCPConnector(limit=50, ttl_dns_cache=300)
        http_session = aiohttp.ClientSession(connector=connector)
    return http_session

#===============================
#~~~~~~~BROADCAST GLOBALS~~~~~~~
#===============================
broadcast_running = False
broadcast_paused = False
broadcast_cancelled = False

# --- CONFIGURATION ---
API_ID = 29515073  
API_HASH = "17a8c38ec658c363675e6ffdf5ce2a42"  
BOT_TOKEN = "8982779566:AAF_4Uy_iwY_GkKze0hJZb8tcp3eL744tkQ"
MAIN_BOT_USERNAME = "YourBotUsername" # Automatically updated on start
OWNERS = [8735285838, 5891100508, 6429574702] # Admin & Owner IDs combined logic
CHANNEL_BUTTON_LINK = "https://t.me/Anime_hindi_Flixx"
BACKUP_CHANNEL_ID = -1003311023133 
IMG_URL = "https://i.ibb.co/RpMQm17y/IMG-20260513-092625-516.jpg" 

LOYAL_MSG = "<b>Tumhe Mere  Owner 💝 Ne Ye Command Use Karne ka Permission Nhi Diya Hai</b>"

# --- SHORTENER CONFIG ---
SHORTENER_URL = "https://lksfy.com/api" 
SHORTENER_API = "c33dd6443d611c3dce8c68c092c89c25d58200c1"
TUTORIAL_LINK = "https://t.me/How_to_open_link_Shortners/22" 

BYPASS_TIME_LIMIT = 65  
TOKEN_EXPIRY_MINUTES = 20

# --- GLOBAL DEFAULT TEXT TEMPLATES ---
DEFAULT_START_CAPTION = """ ʜᴇʏ {message.from_user.mention}
✦ 𝗘𝗹𝘆𝘀𝗶𝘂𝗺 𝗙𝗜𝗟𝗘 𝗕𝗢𝗧  

ɪ’ᴍ ᴢᴜɪɪ — ʏᴏᴜʀ ᴄᴜᴛᴇ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ 💌  

📦 sᴛᴏʀᴇ ʏᴏᴜʀ ғɪʟᴇꜱ ᴇᴀꜱɪʟʏ  
🔗 ᴀᴄᴄᴇꜱꜱ ᴛʜᴇᴍ ᴀɴʏᴛɪᴍᴇ ᴠɪᴀ ʟɪɴᴋꜱ  ✨

💗 ɪ'ʟʟ ᴍᴀᴋᴇ ɪᴛ ᴡᴏʀᴋ ᴘᴇʀꜰᴇᴄᴛʟʏ ꜰᴏʀ ʏᴏᴜ, ᴏᴋᴀʏ? 💞"""

DEFAULT_WARN_TEXT = "⚠️ **ɪᴍᴘᴏʀᴛᴀɴᴛ:**\n\n**ᴀʟʟ ᴍᴇꜱꜱᴀɢᴇꜱ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴡɪᴛʜɪɴ {readable} **\n**ᴘʟᴇᴀꜱᴇ ꜱᴀᴠᴇ ᴏʀ ꜰᴏʀᴡᴀʀᴅ ᴛʜᴇᴍ ᴛᴏ ʏᴏᴜʀ ᴘᴇʀꜱᴏɴᴀʟ ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ  ✨**\n**ᴏᴛʜᴇʀᴡɪꜱᴇ, ʏᴏᴜ ᴡɪʟʟ ʟᴏꜱᴇ ᴛʜᴇᴍ  💞**"
DEFAULT_SHORTNER_TEXT = "**Your link is ready!** 💞\n\nSolve the shortener to get your files👇"
DEFAULT_BYPASS_TEXT = "**Bypass detected!** 😤\n\nKabhi Khud Se Bhi linkshortner solve karlo Ye lo Ab khud se Solve karo."
DEFAULT_FORCESUB_TEXT = "**ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ᴛʜᴇ ᴄʜᴀɴɴᴇʟꜱ ʏᴇᴛ 🌸**\n**ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏʀ ꜱᴇɴᴅ ᴀ ʀᴇզᴜᴇꜱᴛ ᴛᴏ ᴛʜᴇ ᴄʜᴀɴɴᴇʟꜱ ʙᴇʟᴏᴡ💞**"
DEFAULT_BTN_NAME = "📢 𝚄𝚙𝚍𝚊𝚝𝚎 𝙲𝚑𝚊𝚗𝚗𝚎𝚕"

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- MONGODB DATABASE LAYER (DYNAMIC ISOLATION) ---

MONGO_URL = f"mongodb+srv://Kittux_db_user:Ujjal07@cluster0.gvg2umn.mongodb.net/?appName=Cluster0"


class MongoDatabase:
    def __init__(self, uri, bot_id):
        self.client = MongoClient(uri)
        # Har bot ke liye alag database banega (e.g. FileStoreBot_12345678)
        self.db = self.client[f"FileStoreBot_{bot_id}"]
        
        self.settings = self.db["settings"]
        self.batches = self.db["batches"]
        self.forcesub = self.db["forcesub"]
        self.members = self.db["members"]
        self.join_requests = self.db["join_requests"]
        self.left_members = self.db["left_members"]
        self.tokens = self.db["tokens"]
        self.admins = self.db["admins"]
        self.admin_permissions = self.db["admin_permissions"]
        self.banned_users = self.db["banned_users"]
        self.clones = self.db["clones"]
        self.premiums = self.db["premiums"] # 👈 YE LINE ADD KAREIN

    # ---------------- SETTINGS ----------------
    def get_setting(self, key: str, default=None):
        doc = self.settings.find_one({"key": key})
        return doc["value"] if doc else default

    def set_setting(self, key: str, value):
        self.settings.update_one({"key": key}, {"$set": {"value": str(value)}}, upsert=True)

    # ---------------- BATCH ----------------
    def add_batch(self, unique_id: str, messages: list, protect: bool, link_mode: int = 0, successful_clicks="[]"):
        self.batches.update_one(
            {"unique_id": unique_id},
            {"$set": {
                "messages": json.dumps(messages),
                "protect_content": 1 if protect else 0,
                "link_mode": link_mode,
                "successful_clicks": successful_clicks
            }},
            upsert=True
        )
        
    def get_batch(self, unique_id: str):
        doc = self.batches.find_one({"unique_id": unique_id})
        if doc:
            return (doc.get("messages"), doc.get("protect_content", 0), doc.get("link_mode", 0), doc.get("successful_clicks", "[]"))
        return None

    def update_batch_clicks(self, unique_id: str, successful_clicks: str):
        self.batches.update_one({"unique_id": unique_id}, {"$set": {"successful_clicks": successful_clicks}})

    # ---------------- FORCESUB ----------------
    def add_forcesub(self, channel_id: int):
        self.forcesub.update_one({"channel_id": channel_id}, {"$set": {"channel_id": channel_id}}, upsert=True)
        return True

    def remove_forcesub(self, channel_id: int):
        self.forcesub.delete_one({"channel_id": channel_id})

    def get_all_forcesub(self):
        return [doc["channel_id"] for doc in self.forcesub.find()]

    # ---------------- MEMBER TRACKING ----------------
    def update_member(self, user_id: int, status: str):
        self.members.update_one({"user_id": user_id}, {"$set": {"status": status, "joined_at": datetime.now()}}, upsert=True)

    def is_whitelisted(self, user_id: int):
        doc = self.members.find_one({"user_id": user_id})
        return doc and doc.get("status") == "member"

    # ---------------- JOIN REQUEST ----------------
    def add_join_request(self, user_id: int):
        self.join_requests.update_one({"user_id": user_id}, {"$set": {"requested_at": datetime.now()}}, upsert=True)

    def remove_join_request(self, user_id: int):
        self.join_requests.delete_one({"user_id": user_id})

    def is_join_requested(self, user_id: int):
        return self.join_requests.find_one({"user_id": user_id}) is not None

    # ---------------- LEFT MEMBER BLOCKLIST ----------------
    def add_left_member(self, user_id: int):
        self.left_members.update_one({"user_id": user_id}, {"$set": {"left_at": datetime.now()}}, upsert=True)

    def remove_left_member(self, user_id: int):
        self.left_members.delete_one({"user_id": user_id})

    def is_left_member(self, user_id: int):
        return self.left_members.find_one({"user_id": user_id}) is not None

    def clean_all_users(self):
        self.members.delete_many({})
        self.join_requests.delete_many({})
        self.left_members.delete_many({})

    def get_stats_counts(self):
        stats = {}
        stats['white_users'] = self.members.count_documents({"status": "member"})
        stats['forcesub'] = self.forcesub.count_documents({})
        stats['block_users'] = self.left_members.count_documents({})
        stats['total_users'] = self.members.count_documents({})
        return stats

    # ---------------- TOKENS ----------------
    def add_token(self, token, batch_id, created_at, user_id):
        self.tokens.insert_one({
            "token": token, "batch_id": batch_id, "created_at": created_at, "user_id": user_id
        })

    def get_token(self, token):
        return self.tokens.find_one({"token": token})

    def delete_token(self, token):
        self.tokens.delete_one({"token": token})

    # ---------------- BAN & ADMIN ----------------
    def is_banned(self, user_id: int):
        return self.banned_users.find_one({"user_id": user_id}) is not None

    def is_admin(self, user_id: int):
        return user_id in OWNERS or self.admins.find_one({"user_id": user_id}) is not None

    def has_permission(self, user_id: int, perm: str):
        if user_id in OWNERS: return True
        return self.admin_permissions.find_one({"user_id": user_id}) is not None

    # ---------------- CLONES ----------------
    def add_clone(self, bot_id, token, owner_id):
        self.clones.update_one({"bot_id": bot_id}, {"$set": {"token": token, "owner_id": owner_id}}, upsert=True)
    
    def get_all_clones(self):
        return list(self.clones.find())

    # ----------- PREMIUM USERS -----------
    def add_premium(self, user_id: int, full_name: str):
        self.premiums.update_one({"user_id": user_id}, {"$set": {"full_name": full_name}}, upsert=True)

    def remove_premium(self, user_id: int):
        self.premiums.delete_one({"user_id": user_id})

    def is_premium(self, user_id: int):
        return self.premiums.find_one({"user_id": user_id}) is not None

    def get_all_premiums(self):
        return list(self.premiums.find())

    # ----------- SEPARATE BOT IMAGE STORAGE -----------
    def set_bot_img(self, bot_id: int, file_id: str):
        self.settings.update_one({"key": f"IMG_{bot_id}"}, {"$set": {"value": file_id}}, upsert=True)

    def get_bot_img(self, bot_id: int, default: str):
        doc = self.settings.find_one({"key": f"IMG_{bot_id}"})
        return doc["value"] if doc else default

    def remove_bot_img(self, bot_id: int):
        self.settings.delete_one({"key": f"IMG_{bot_id}"})

    # ---------------- CUSTOMIZATION SYSTEM ----------------
    def get_custom_msg(self, bot_id: int, key: str, default: str) -> str:
        doc = self.settings.find_one({"key": f"CUSTOM_{key}_{bot_id}"})
        return doc["value"] if doc else default

    def set_custom_msg(self, bot_id: int, key: str, value: str):
        self.settings.update_one({"key": f"CUSTOM_{key}_{bot_id}"}, {"$set": {"value": value}}, upsert=True)
        
    # ---------------- BACKUP & RESTORE ----------------
    def export_data(self):
        data = {}
        collections = self.db.list_collection_names()
        for coll in collections:
            docs = list(self.db[coll].find({}, {"_id": 0}))
            data[coll] = {"rows": docs, "type": "mongodb"}
        return data

    def import_data(self, data):
        for coll_name, coll_data in data.items():
            if coll_name == "created_at": continue
            
            if isinstance(coll_data, dict) and "columns" in coll_data:
                cols = coll_data["columns"]
                rows = coll_data["rows"]
                docs = []
                for row in rows:
                    doc = {cols[i]: row[i] for i in range(len(cols))}
                    docs.append(doc)
                if docs:
                    self.db[coll_name].delete_many({})
                    self.db[coll_name].insert_many(docs)
            
            elif isinstance(coll_data, dict) and coll_data.get("type") == "mongodb":
                docs = coll_data.get("rows", [])
                if docs:
                    self.db[coll_name].delete_many({})
                    self.db[coll_name].insert_many(docs)
            
            elif isinstance(coll_data, list) and coll_data:
                pass 

    # ---------------- DUAL SHORTENER SETTINGS ----------------
    def get_shortener_config(self, index: int):
        """Index can be 1 or 2"""
        doc = self.settings.find_one({"key": f"SHORTENER_CONFIG_{index}"})
        if doc and isinstance(doc.get("value"), dict):
            return doc["value"]
        # Default fallback coordinates
        return {
            "url": SHORTENER_URL if index == 1 else "",
            "api": SHORTENER_API if index == 1 else "",
            "tut": TUTORIAL_LINK if index == 1 else "",
            "time": BYPASS_TIME_LIMIT if index == 1 else 65
        }

    def set_shortener_config(self, index: int, config_dict: dict):
        self.settings.update_one({"key": f"SHORTENER_CONFIG_{index}"}, {"$set": {"value": config_dict}}, upsert=True)


# Dynamic Database Getter
_db_cache = {}
def get_db(bot_id):
    if bot_id not in _db_cache:
        _db_cache[bot_id] = MongoDatabase(MONGO_URL, bot_id)
    return _db_cache[bot_id]

# --- UTILITIES ---
def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

def parse_duration(duration_str: str) -> Optional[int]:
    total_seconds = 0
    tokens = duration_str.lower().split()
    for i in range(len(tokens)):
        if tokens[i].isdigit():
            val = int(tokens[i])
            if i + 1 < len(tokens):
                unit = tokens[i+1]
                if 'hour' in unit: total_seconds += val * 3600
                elif 'min' in unit: total_seconds += val * 60
                elif 'sec' in unit: total_seconds += val
    return total_seconds if total_seconds > 0 else None

def delete_token(client, token):
    client.bot_db.delete_token(token)


	


# Link Generation Update with Alternate Routing Logic
async def create_short_link(client, long_url):
    config1 = client.bot_db.get_shortener_config(1)
    config2 = client.bot_db.get_shortener_config(2)
    
    active1 = client.bot_db.get_setting("SHORTENER_1_ACTIVE", "1") == "1"
    active2 = client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "1"
    
    # Check if slot 1 contains custom configurations or standard hardcoded configurations
    is_slot1_custom = (config1.get("api") and config1.get("api") != SHORTENER_API)
    
    selected_config = config1
    
    # Dual-routing logic matrix implementation
    if active1 and active2 and is_slot1_custom and config2.get("api"):
        current_counter = int(client.bot_db.get_setting("ROUTING_COUNTER", "0"))
        if current_counter % 2 == 0:
            selected_config = config1
        else:
            selected_config = config2
        client.bot_db.set_setting("ROUTING_COUNTER", str(current_counter + 1))
    elif active2 and config2.get("api"):
        selected_config = config2
    else:
        # Fallback tracking targeting Slot 1 (Custom configuration gets priority over base default system)
        selected_config = config1

    api_key = selected_config.get("api")
    api_url = selected_config.get("url")
    
    if not api_key or not api_url:
        return None
        
    params = {'api': api_key, 'url': long_url, 'format': 'text'}
    try:
        session = await get_session()
        async with session.get(api_url, params=params, timeout=7) as resp:
            if resp.status == 200:
                res_text = await resp.text()
                if "{" in res_text:
                    try:
                        data = await resp.json()
                        return data.get("shortenedUrl") or data.get("link") or data.get("shortened")
                    except: return None
                return res_text.strip()
    except Exception as e:
        logger.error(f"Link Generation Failed: {e}")
        return None


def generate_token(client, user_id, batch_id):
    token_id = str(uuid.uuid4())[:8]
    token = f"tok_{token_id}_{batch_id}"
    client.bot_db.add_token(token, batch_id, int(time.time()), user_id)
    return token
    
# Active Bypass Validation Layer based on Selected Active Shortener Rules
def validate_token(client, token, user_id):
    row = client.bot_db.get_token(token)
    if not row: return None, "invalid"

    batch_id = row["batch_id"]
    created_at = row["created_at"]
    db_user_id = row["user_id"]

    if db_user_id != user_id: return None, "invalid"
    if time.time() - created_at > TOKEN_EXPIRY_MINUTES * 60: return None, "expired"

    # Match exact active shortener bypass ceiling threshold parameters
    config1 = client.bot_db.get_shortener_config(1)
    config2 = client.bot_db.get_shortener_config(2)
    active2 = client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "1"
    
    current_bypass_time = int(config2.get("time", 65)) if active2 and config2.get("api") else int(config1.get("time", 65))
    
    if time.time() - created_at < current_bypass_time:
        return batch_id, "bypass"
    return batch_id, "valid"

# # ================= AUTOMATICALLY BACK UPLOAD CHANNEL=============
async def auto_cloud_backup(application):    
    await asyncio.sleep(5)    
    while True:    
        try:
            ist_timezone = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist_timezone)    
            target = now.replace(hour=23, minute=59, second=59, microsecond=0)    
            if now >= target: target += timedelta(days=1)    
            wait_seconds = (target - now).total_seconds()    
            await asyncio.sleep(wait_seconds)    
    
            backup_data = application.bot_db.export_data()
            backup_data["created_at"] = datetime.utcnow().isoformat()    
    
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as f:    
                json.dump(backup_data, f, indent=2, default=str)    
                file_path = f.name   
    
            old_msg_id_str = application.bot_db.get_setting("last_backup_msg_id")
            old_msg_id = int(old_msg_id_str) if old_msg_id_str else None
    
            msg = await application.send_document(    
                chat_id=BACKUP_CHANNEL_ID,    
                document=file_path,    
                file_name=f"Sarena_Backup_{now.strftime('%d_%m_%Y')}.json",    
                caption="**🌙 Daily Auto Backup**\n\n✅ Link Mode & Batches Saved."    
            )    
    
            application.bot_db.set_setting("last_backup_msg_id", str(msg.id))
            if os.path.exists(file_path): os.remove(file_path)    
    
            if old_msg_id:
                await asyncio.sleep(300)
                try: await application.delete_messages(BACKUP_CHANNEL_ID, old_msg_id)    
                except: pass
        except Exception as e:    
            logger.error(f"Auto Backup Loop Error: {e}")
            
# --- BOT CLIENT ---
active_clones = []

class FileStoreBot(Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collecting_users = {}
        # Dynamic Database attachment for this specific bot instance
        bot_token = kwargs.get("bot_token")
        if bot_token:
            self.bot_id = int(bot_token.split(":")[0])
            self.bot_db = get_db(self.bot_id)
        else:
            self.bot_id = None
            self.bot_db = None

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username = me.username
        global MAIN_BOT_USERNAME
        if not getattr(self, "is_clone", False):
            MAIN_BOT_USERNAME = self.username
        logger.info(f"Bot started as @{self.username}")
        if not getattr(self, "is_clone", False):
            asyncio.create_task(auto_cloud_backup(self))

    async def stop(self, *args):
        await super().stop()
        logger.info("Bot stopped.")

bot = FileStoreBot(name="FileStoreBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, plugins=None, workers=100)

# --- FILTERS ---
async def check_ban_status(_, client, message: Message):
    if not message.from_user: return False
    if client.bot_db.is_banned(message.from_user.id):
        raise ContinuePropagation 
    return True
ban_filter = filters.create(check_ban_status)

async def admin_filter(_, client, message: Message):
    if not message.from_user: return False
    is_owner = message.from_user.id in OWNERS
    if getattr(client, "is_clone", False) and getattr(client, "clone_owner", None) == message.from_user.id:
        is_owner = True
    return is_owner or client.bot_db.is_admin(message.from_user.id)
is_admin = filters.create(admin_filter)

# --- CORE LOGIC: FORCESUB ---
async def check_user_status(client, user_id: int):
    channels = client.bot_db.get_all_forcesub()
    if not channels: return True, []
    must_join = []
    for chat_id in channels:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: continue
            elif member.status == enums.ChatMemberStatus.RESTRICTED: continue
            else:
                if not client.bot_db.is_join_requested(user_id): must_join.append(chat_id)
        except UserNotParticipant:
            if not client.bot_db.is_join_requested(user_id): must_join.append(chat_id)
        except Exception as e:
            logger.error(f"Error checking {chat_id}: {e}")
            must_join.append(chat_id)
    return len(must_join) == 0, must_join

async def get_invite_link(client, chat_id: int):
    try:
        link = await client.create_chat_invite_link(
            chat_id=chat_id, expire_date=datetime.now() + timedelta(minutes=15), creates_join_request=True
        )
        return link.invite_link
    except Exception as e:
        logger.error(f"Invite link error: {e}")
        try:
            chat = await client.get_chat(chat_id)
            if chat.username: return f"https://t.me/{chat.username}"
        except: pass
        return None

# --- ADMIN / OWNER MANAGEMENT ---
@bot.on_message(ban_filter & filters.command("add_admin") & filters.private)
async def add_admin(client, message: Message):
    if message.from_user.id not in OWNERS:
        return await message.reply(LOYAL_MSG, parse_mode=enums.ParseMode.HTML)
    if len(message.command) < 2:
        return await message.reply("⚠ User ID missing")
    try: uid = int(message.command[1])
    except ValueError: return await message.reply("🍁 Invalid User ID Format")
    
    try: 
        user = await client.get_users(uid)
        user_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception as e: 
        return await message.reply(f"🍁 Invalid User ID or Bot not in chat: {e}")

    client.bot_db.admins.update_one(
        {"user_id": uid}, 
        {"$set": {"full_name": user_name, "phone": getattr(user, 'phone_number', None)}}, 
        upsert=True
    )
    client.bot_db.admin_permissions.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)

    text = f"<b>ᴀᴅᴍɪɴ:</b> <a href='tg://openmessage?user_id={uid}'>{user_name}</a>\n<b>🆔 ɪᴅ :</b> <code>{uid}</code>"
    button = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={uid}")]])                  
    await message.reply(text, parse_mode=enums.ParseMode.HTML, reply_markup=button)

@bot.on_message(ban_filter & filters.command("remove_admin") & filters.private)
async def remove_admin(client, message: Message):
    if message.from_user.id not in OWNERS:
        return await message.reply(LOYAL_MSG, parse_mode=enums.ParseMode.HTML)
    if len(message.command) < 2: return await message.reply("⚠ User ID missing")
    try: uid = int(message.command[1])
    except ValueError: return await message.reply("🍁 Invalid User ID Format")

    row = client.bot_db.admins.find_one({"user_id": uid})
    if not row: return await message.reply("🍁 User is not admin")
    try:
        user = await client.get_users(uid)
        latest_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except: 
        latest_name = row.get("full_name", "Unknown")

    client.bot_db.admins.delete_one({"user_id": uid})
    client.bot_db.admin_permissions.delete_one({"user_id": uid})

    safe_name = html.escape(latest_name)
    text = f"<b>{safe_name} 🤭\nᴀʙ ᴀᴅᴍɪɴ ɴᴀʜɪ ʀᴀʜᴇ 💔\n\n✔️ sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ\n🆔 ɪᴅ :{uid}</b>"  
    button = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={uid}")]])  
    await message.reply(text, parse_mode=enums.ParseMode.HTML, reply_markup=button)

@bot.on_message(ban_filter & filters.command("admin_list") & filters.private)
async def admin_list(client, message: Message):
    if message.from_user.id not in OWNERS:
        return await message.reply(LOYAL_MSG, parse_mode=enums.ParseMode.HTML)
    await message.reply("<b>👑ʜᴇʏ sᴇɴᴘᴀɪ!\nʏᴀʜᴀɴ sᴀʀᴇ ᴀᴅᴍɪɴs ᴅɪᴋʜ ʀᴀʜᴇ ʜᴀɪɴ 👇💗</b>", parse_mode=enums.ParseMode.HTML)
    rows = list(client.bot_db.admins.find())
    if not rows: return await message.reply("⚠ No Extra Admins")
    for row in rows:
        uid, name, phone = row["user_id"], row.get("full_name", "Unknown"), row.get("phone", "N/A")
        try: 
            user = await client.get_users(uid)
            latest_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
        except: 
            latest_name = name
        safe_name = latest_name.replace("<", "&lt;").replace(">", "&gt;")
        text = f"<b>𓆰♕𓆪ᴀᴅᴍɪɴs:</b> <a href='tg://openmessage?user_id={uid}'>{safe_name}</a>\n<b>🆔 ɪᴅ :</b> <code>{uid}</code>\n<b>📞 ᴘʜᴏɴᴇ :</b> <code>{phone}</code>"  
        button = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={uid}")]])                  
        await message.reply(text, parse_mode=enums.ParseMode.HTML, reply_markup=button, disable_web_page_preview=True)  
        await asyncio.sleep(0.3)

@bot.on_message(ban_filter & filters.command("ban") & is_admin)
async def ban_user(client, message: Message):
    if not client.bot_db.has_permission(message.from_user.id, "ban_user"):
        return await message.reply("<b>Tumhe Mere Lord Black 💝 Ne Ye Command Use Karne ka Permission Nhi Diya Hai</b>", parse_mode=enums.ParseMode.HTML)
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply("*⚠ User ID Missing*")
    uid = int(message.command[1])
    if client.bot_db.is_admin(uid) or uid in OWNERS:
        return await message.reply("*🍁 Admin ko ban karne se pehle admin se hatao*")
    try: 
        user = await client.get_users(uid)
        full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")        
    except Exception: 
        full_name = "Unknown User"        
    
    client.bot_db.banned_users.update_one({"user_id": uid}, {"$set": {"full_name": full_name, "date": datetime.utcnow().isoformat()}}, upsert=True)
    safe_name = html.escape(full_name)        
    
    text = f"🚫 <a href='tg://openmessage?user_id={uid}'>{safe_name}</a> 🤭\nᴀʙ ʙᴀɴ ʜᴏ ɢᴀʏᴀ 💔\n\n<b>🆔 ɪᴅ:</b> <code>{uid}</code>"        
    button = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={uid}")]])        
    try: await message.reply(text, parse_mode=enums.ParseMode.HTML, reply_markup=button)
    except Exception as e: print(e)

@bot.on_message(ban_filter & filters.command("unban") & is_admin)
async def unban_user(client, message: Message):
    if not client.bot_db.has_permission(message.from_user.id, "unban_user"):
        return await message.reply("<b>Tumhe Mere Owner💝 Ne Ye Command Use Karne ka Permission Nhi Diya Hai</b>", parse_mode=enums.ParseMode.HTML)
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply("*⚠ User ID Missing*")
    uid = int(message.command[1])
    row = client.bot_db.banned_users.find_one({"user_id": uid})
    if not row: return await message.reply("*⚠ User Already Unbanned*")
    client.bot_db.banned_users.delete_one({"user_id": uid})
    safe_name = html.escape(row.get("full_name", "User"))        
    try: await client.send_message(uid, f"<b>{safe_name}</b> 💝\n\nᴀʙ ᴛᴜᴍ ғʀᴇᴇ ʜᴏ 🤭\nʟᴏʀᴅ ʙʟᴀᴄᴋ ɴᴇ ᴛᴜᴍʜᴇ ᴜɴʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ 💗✨", parse_mode=enums.ParseMode.HTML)        
    except Exception: pass        
    text = f"<b>🍀 ᴜsᴇʀ ᴜɴʙᴀɴᴇᴅ 🌸</b>\n\n<b>ᴜsᴇʀ:</b> <a href='tg://openmessage?user_id={uid}'>{safe_name}</a>\n<b>🆔 ɪᴅ:</b> <code>{uid}</code>"        
    button = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={uid}")]])        
    try: await message.reply(text, parse_mode=enums.ParseMode.HTML, reply_markup=button)
    except Exception as e: print(e)

# --- BAN LIST COMMAND ---
@bot.on_message(ban_filter & filters.command("ban_list") & is_admin & filters.private)
async def ban_list_cmd(client, message: Message):
    banned_users = list(client.bot_db.banned_users.find())
    
    if not banned_users:
        return await message.reply("<b>🚫 Koyi bhi user abhi ban nahi hai.</b>", parse_mode=enums.ParseMode.HTML)
    
    await message.reply("<b>📋 ʙᴀɴɴᴇᴅ ᴜsᴇʀs ʟɪsᴛ 👇</b>", parse_mode=enums.ParseMode.HTML)
    
    for row in banned_users:
        uid = row["user_id"]
        user_name = row.get("full_name", "Unknown User")
        safe_name = html.escape(user_name)
        
        text = f"<b>🚫 ʙᴀɴɴᴇᴅ ᴜsᴇʀ:</b> <a href='tg://openmessage?user_id={uid}'>{safe_name}</a>\n<b>🆔 ɪᴅ :</b> <code>{uid}</code>"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={uid}")],
            [InlineKeyboardButton("𝗥𝗘𝗠𝗢𝗩𝗘 𝗨𝗦𝗘𝗥 ❌", callback_data=f"unban_user_{uid}")]
        ])
        
        try:
            await message.reply(text, parse_mode=enums.ParseMode.HTML, reply_markup=buttons, disable_web_page_preview=True)
            await asyncio.sleep(0.3) # FloodWait se bachne ke liye thoda delay
        except Exception as e:
            logger.error(f"Ban list message error: {e}")

# --- REMOVE USER (UNBAN) BUTTON CALLBACK ---
@bot.on_callback_query(filters.regex(r"^unban_user_"))
async def unban_user_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    
    # Check permission: Sirf Owners (Main bot owners ya clone owners) hi click kar sakte hain
    is_main_owner = user_id in OWNERS
    is_clone_owner = getattr(client, "is_clone", False) and getattr(client, "clone_owner", None) == user_id
    
    if not (is_main_owner or is_clone_owner):
        return await query.answer("❌ Ye button sirf Owners use kar sakte hain!", show_alert=True)
        
    target_uid = int(query.data.split("_")[2])
    
    # Check agar user already unban ho chuka ho
    row = client.bot_db.banned_users.find_one({"user_id": target_uid})
    if not row:
        return await query.answer("⚠️ User pehle hi unban ho chuka hai.", show_alert=True)
        
    # Unban process
    client.bot_db.banned_users.delete_one({"user_id": target_uid})
    safe_name = html.escape(row.get("full_name", "User"))
    
    # Try sending message to the user notifying them of the unban
    try: 
        await client.send_message(target_uid, f"<b>{safe_name}</b> 💝\n\nᴀʙ ᴛᴜᴍ ғʀᴇᴇ ʜᴏ 🤭\nʟᴏʀᴅ ʙʟᴀᴄᴋ ɴᴇ ᴛᴜᴍʜᴇ ᴜɴʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ 💗✨", parse_mode=enums.ParseMode.HTML)        
    except Exception: 
        pass  
        
    await query.answer("✅ User successfully unbanned!", show_alert=True)
    
    # Message ko update karna taaki dobara koi click na kare
    updated_text = f"<b>🍀 ᴜsᴇʀ ᴜɴʙᴀɴᴇᴅ 🌸</b>\n\n<b>ᴜsᴇʀ:</b> <a href='tg://openmessage?user_id={target_uid}'>{safe_name}</a>\n<b>🆔 ɪᴅ:</b> <code>{target_uid}</code>\n\n<i>✅ Successfully Removed by Owner</i>"
    button = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={target_uid}")]])
    
    await query.message.edit_text(updated_text, parse_mode=enums.ParseMode.HTML, reply_markup=button)


# --- IN-MEMORY DICTIONARY FOR PREVIEW & TIMEOUT CONTROL ---
# Structure: { user_id: {"msg_id": 123, "mode": "start_msg", "text": "...", "timestamp": 1234} }
customize_sessions = {}

async def customize_timeout_cleaner(client, user_id: int, chat_id: int, msg_id: int):
    """10 Minutes dynamic inactivity monitor tracking rule"""
    await asyncio.sleep(600)  # 10 Minutes = 600 seconds
    if user_id in customize_sessions and customize_sessions[user_id].get("msg_id") == msg_id:
        customize_sessions.pop(user_id, None)
        try:
            await client.delete_messages(chat_id, msg_id)
        except:
            pass

def get_customize_menu():
    text = "⚙️ **𝖶𝗁𝖺𝗍 𝖽𝗈 𝗒𝗈𝗎 𝗐𝖺𝗇𝗍 𝗍𝗈 𝖼𝗎𝗌𝗍𝗈𝗆𝗂𝗓𝖾?**\n\n𝖲𝖾𝗅𝖾𝖼𝗍 𝖺𝗇𝗒 𝗈𝖿 𝗍𝗁𝖾 𝖿𝗈𝗅𝗅𝗈𝗐𝗂𝗇𝗀 parameters 𝖻𝖾𝗅𝗈𝗐 𝗍𝗈 modify 𝗒𝗈𝗎𝗋 𝖻𝗈𝗍'𝗌 layout dynamic configuration layers."
    buttons = [
        [InlineKeyboardButton("📝 Start Msg", callback_data="cust_start_msg"), InlineKeyboardButton("🔘 Update BTN", callback_data="cust_update_btn")],
        [InlineKeyboardButton("⌛ Auto del Msg", callback_data="cust_autodel_msg"), InlineKeyboardButton("🔗 Shortner Msg", callback_data="cust_short_msg")],
        [InlineKeyboardButton("🛰️ Forcesub Msg", callback_data="cust_forcesub_msg")]
    ]
    return text, InlineKeyboardMarkup(buttons)

@bot.on_message(ban_filter & filters.command("customize") & is_admin & filters.private)
async def customize_cmd_handler(client, message: Message):
    user_id = message.from_user.id
    text, markup = get_customize_menu()
    sent_msg = await message.reply(text, reply_markup=markup)
    
    # Register customization monitor tracking state session
    customize_sessions[user_id] = {
        "msg_id": sent_msg.id,
        "mode": "main_menu",
        "timestamp": time.time()
    }
    # Create self-destruction clock loop task
    asyncio.create_task(customize_timeout_cleaner(client, user_id, message.chat.id, sent_msg.id))


# --- DYNAMIC CUSTOMIZATION ROUTER CALLBACK HANDLER ---
@bot.on_callback_query(filters.regex(r"^cust_"))
async def customize_callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    bot_id = client.me.id

    if user_id not in customize_sessions or customize_sessions[user_id]["msg_id"] != query.message.id:
        return await query.answer("⚠️ Session Expired! Please execute /customize command once again.", show_alert=True)

    customize_sessions[user_id]["timestamp"] = time.time()
    back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="cust_back_main")]])

    if data == "cust_back_main":
        customize_sessions[user_id]["mode"] = "main_menu"
        text, markup = get_customize_menu()
        return await query.message.edit_text(text, reply_markup=markup)

    elif data == "cust_start_msg":
        current = client.bot_db.get_custom_msg(bot_id, "START_CAPTION", DEFAULT_START_CAPTION)
        customize_sessions[user_id]["mode"] = "wait_start"
        text = f"📑 **Current Configuration:**\n\n{current}\n\n━━━━━━━━━━━━━━━━━━━━\n📥 **Send Your Msg To Set /Start Msg Caption**"
        return await query.message.edit_text(text, reply_markup=back_markup)

    elif data == "cust_autodel_msg":
        current = client.bot_db.get_custom_msg(bot_id, "AUTODEL", DEFAULT_WARN_TEXT)
        customize_sessions[user_id]["mode"] = "wait_autodel"
        text = f"📑 **Current Configuration:**\n\n{current}\n\n━━━━━━━━━━━━━━━━━━━━\n📥 **Send Your Auto delete Msg With {{readable}} placeholder**"
        return await query.message.edit_text(text, reply_markup=back_markup)

    elif data == "cust_forcesub_msg":
        current = client.bot_db.get_custom_msg(bot_id, "FORCESUB", DEFAULT_FORCESUB_TEXT)
        customize_sessions[user_id]["mode"] = "wait_forcesub"
        text = f"📑 **Current Configuration:**\n\n{current}\n\n━━━━━━━━━━━━━━━━━━━━\n📥 **Send your forcesub msg**"
        return await query.message.edit_text(text, reply_markup=back_markup)

    elif data == "cust_short_msg":
        text = "🎯 **Select your msg to customize:**"
        sub_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Shortner", callback_data="cust_target_shortner"), 
             InlineKeyboardButton("On Bypass Detect 😤", callback_data="cust_target_bypass")],
            [InlineKeyboardButton("🔙 Back", callback_data="cust_back_main")]
        ])
        return await query.message.edit_text(text, reply_markup=sub_kb)

    elif data == "cust_target_shortner":
        customize_sessions[user_id]["mode"] = "wait_shortner"
        return await query.message.edit_text("📥 **Send your msg (For Shortener Link Ready Screen):**", reply_markup=back_markup)

    elif data == "cust_target_bypass":
        customize_sessions[user_id]["mode"] = "wait_bypass"
        return await query.message.edit_text("📥 **Send your msg (For Bypass Detected Screen):**", reply_markup=back_markup)

    elif data == "cust_update_btn":
        text = "🔘 **Select what you want to change (Button Name or Link Target):**"
        btn_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏷️ Change Btn Name", callback_data="cust_btn_name"),
             InlineKeyboardButton("🔗 Change Btn Link", callback_data="cust_btn_link")],
            [InlineKeyboardButton("🔙 Back", callback_data="cust_back_main")]
        ])
        return await query.message.edit_text(text, reply_markup=btn_kb)

    elif data == "cust_btn_name":
        customize_sessions[user_id]["mode"] = "wait_btn_name"
        return await query.message.edit_text("📥 **Send Your button name:**", reply_markup=back_markup)

    elif data == "cust_btn_link":
        customize_sessions[user_id]["mode"] = "wait_btn_link"
        return await query.message.edit_text("📥 **Send your button URL link:**", reply_markup=back_markup)

    elif data.startswith("cust_save_"):
        key_target = data.replace("cust_save_", "")
        pending_text = customize_sessions[user_id].get("text")
        if pending_text:
            client.bot_db.set_custom_msg(bot_id, key_target, pending_text)
            await query.answer("✅ Saved layout settings securely into MongoDB cluster matrix!", show_alert=True)
        
        customize_sessions[user_id]["mode"] = "main_menu"
        text, markup = get_customize_menu()
        return await query.message.edit_text(text, reply_markup=markup)



        
#============ image Set /img =========================
@bot.on_message(ban_filter & filters.command("img") & is_admin & filters.private)
async def dynamic_image_handler(client, message: Message):
    bot_id = client.me.id
    
    # Handle deletion switch parameter state
    if len(message.command) > 1 and message.command[1].lower() == "remove":
        client.bot_db.remove_bot_img(bot_id)
        return await message.reply("🔄 **Dynamic display buffer removed. Bot reverted back to hardcoded asset definitions parameters.**")

    # If simple query triggered, execute detailed visualization metadata readout mapping
    if not message.reply_to_message or not message.reply_to_message.photo:
        current_img = client.bot_db.get_bot_img(bot_id, IMG_URL)
        
        # Build evaluation report parameters context data package arrays
        text_report = (
            "🖼️ **𝗖𝘂𝗿𝗿𝗲𝗻𝘁 𝗔𝗰𝘁𝗶𝘃𝗲 𝗠𝗲𝘁𝗮𝗱𝗮𝘁𝗮 𝗔𝘀𝘀𝗲𝘁 𝗟𝗮𝘆𝗲𝗿**\n\n"
            f"🔗 **Asset Source Reference:** `{current_img}`\n\n"
            "💡 **To map explicit unique graphical layouts per bot channel layer, reply to any image using:** `/img`"
        )
        try: return await message.reply_photo(photo=current_img, caption=text_report)
        except: return await message.reply(text_report)

    # Process target configuration asset updates explicitly
    photo_object = message.reply_to_message.photo
    file_id = photo_object.file_id
    file_size = photo_object.file_size
    width = photo_object.width
    height = photo_object.height
    
    client.bot_db.set_bot_img(bot_id, file_id)
    
    analytical_caption = (
        "✅ **𝗚𝗿𝗮𝗽𝗵𝗶𝗰𝗮𝗹 𝗞𝗲𝗿𝗻𝗲𝗹 𝗨𝗽??𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 **Identifier ID:** `{file_id}`\n\n"
        f"📐 **Resolution Dimensions:** `{width} x {height} Pixels`\n"
        f"💾 **Data Size Metrics:** `{round(file_size / 1024, 2)} KB`\n"
        f"🤖 **Layer Context Binding:** @{client.me.username}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✨ **This image configuration will now cleanly render as top primary display layer.**"
    )
    await message.reply_photo(photo=file_id, caption=analytical_caption)
  
# ==========================================
# --- PREMIUM USER COMMANDS ---
# ==========================================
@bot.on_message(ban_filter & filters.command("add_pri") & is_admin & filters.private)
async def add_premium_cmd(client, message: Message):
    if len(message.command) < 2: return await message.reply("⚠ User ID/Username missing")
    try:
        user = await client.get_users(message.command[1])
        uid = user.id
        full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception as e:
        return await message.reply(f"🍁 Invalid User ID/Username: {e}")
    client.bot_db.add_premium(uid, full_name)
    await message.reply(f"✅ **{full_name}** is now a Premium User!")

@bot.on_message(ban_filter & filters.command("rem_pri") & is_admin & filters.private)
async def rem_premium_cmd(client, message: Message):
    if len(message.command) < 2: return await message.reply("⚠ User ID/Username missing")
    try:
        user = await client.get_users(message.command[1])
        uid = user.id
    except:
        if message.command[1].isdigit(): uid = int(message.command[1])
        else: return await message.reply("🍁 Invalid User ID/Username")
    client.bot_db.remove_premium(uid)
    await message.reply(f"✅ Successfully removed from Premium Users!")

@bot.on_message(ban_filter & filters.command("pri_list") & is_admin & filters.private)
async def pri_list_cmd(client, message: Message):
    rows = client.bot_db.get_all_premiums()
    if not rows: return await message.reply("⚠ No Premium Users")
    await message.reply("<b>🌟 ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ʟɪsᴛ 👇</b>", parse_mode=enums.ParseMode.HTML)
    for row in rows:
        uid = row["user_id"]
        name = row.get("full_name", "Unknown")
        safe_name = name.replace("<", "&lt;").replace(">", "&gt;")
        text = f"<b>🌟 ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ:</b> <a href='tg://openmessage?user_id={uid}'>{safe_name}</a>\n<b>🆔 ɪᴅ :</b> <code>{uid}</code>"
        button = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ 🫣✨", url=f"tg://openmessage?user_id={uid}")]])
        await message.reply(text, parse_mode=enums.ParseMode.HTML, reply_markup=button, disable_web_page_preview=True)
        await asyncio.sleep(0.3)

# --- DYNAMIC STORAGE CHANNEL (IMPROVED & PROFESSIONAL) ---
@bot.on_message(ban_filter & filters.command("st") & is_admin & filters.private)
async def set_storage_cmd(client, message: Message):
    # Agar sirf /st likha ho, toh current details dikhao
    if len(message.command) < 2:
        curr_id = client.bot_db.get_setting(f"STORAGE_{client.me.id}")
        if not curr_id:
            return await message.reply(
                "❌ **Storage Channel Not Set!**\n\n"
                "Aapne abhi tak koi storage channel configure nahi kiya hai.\n"
                "💡 **Usage:** `/st -100xxxxxxxxx`",
                parse_mode=enums.ParseMode.HTML
            )
        
        try:
            chat = await client.get_chat(int(curr_id))
            details = (
                "📑 **𝗖𝘂𝗿𝗿𝗲𝗻𝘁 𝗦𝘁𝗼𝗿𝗮𝗴𝗲 𝗗𝗲𝘁𝗮𝗶𝗹𝘀**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Bot:** @{client.me.username}\n"
                f"📢 **Channel:** `{chat.title}`\n"
                f"🆔 **ID:** `{curr_id}`\n"
                f"👥 **Members:** {chat.members_count}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "✨ *Files isi channel mein save hongi.*"
            )
            return await message.reply(details)
        except Exception:
            return await message.reply(f"📑 **Current Storage ID:** `{curr_id}`\n⚠️ *Bot is no longer in this channel or has no access.*")

    # Naya Storage Set karne ka logic
    status_msg = await message.reply("🔍 **Validating Channel & Permissions...**")
    raw_id = message.command[1]
    
    try:
        if not (raw_id.startswith("-100") and raw_id[1:].isdigit()):
            return await status_msg.edit("❌ **Invalid Format!**\n\nPlease provide a valid Channel ID (e.g., `-100123456789`).")
        
        target_id = int(raw_id)
        
        # Check Permissions
        try:
            member = await client.get_chat_member(target_id, "me")
            if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await status_msg.edit("❌ **Permission Denied!**\n\nMain is channel mein Admin nahi hoon. Pehle mujhe Admin banayein.")
            
            if not member.privileges.can_post_messages:
                return await status_msg.edit("❌ **Missing Rights!**\n\nMere paas is channel mein `Post Messages` ki permission nahi hai.")
            
            chat_info = await client.get_chat(target_id)
            
            # Save separately for each bot (Main/Clone)
            client.bot_db.set_setting(f"STORAGE_{client.me.id}", str(target_id))
            
            success_text = (
                "✅ **𝗦𝘁𝗼𝗿𝗮𝗴𝗲 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗨𝗽𝗱𝗮𝘁𝗲𝗱!**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 **Bot:** @{client.me.username}\n"
                f"📡 **Channel:** `{chat_info.title}`\n"
                f"🆔 **ID:** `{target_id}`\n"
                "🔐 **Status:** Fully Connected & Authorized\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "✨ *Ab aap files collect karna start kar sakte hain.*"
            )
            await status_msg.edit(success_text)
            
        except UserNotParticipant:
            await status_msg.edit("❌ **Bot Not Found!**\n\nPehle mujhe us channel mein add karke Admin banayein.")
        except RPCError as e:
            await status_msg.edit(f"❌ **Telegram Error:** `{str(e)}` ")
            
    except ValueError:
        await status_msg.edit("❌ **Invalid ID!** Use numbers only after -100.")
    except Exception as e:
        await status_msg.edit(f"❌ **Fatal Error:** `{str(e)}` ")

def get_storage_id(client):
    # Yeh logic automatically bot-specific ID return karega
    val = client.bot_db.get_setting(f"STORAGE_{client.me.id}")
    return int(val) if val else None

# --- CLONE SYSTEM ---
@bot.on_message(ban_filter & filters.command("clone") & filters.private)
async def clone_bot_cmd(client, message: Message):
    # Clone bot restriction
    if getattr(client, "is_clone", False):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("𝗭𝗨𝗜𝗜 𝗕𝗢𝗧", url=f"https://t.me/{MAIN_BOT_USERNAME}")]])
        return await message.reply("↓ 𝐅𝐨𝐫 𝐜𝐥𝐨𝐧𝐢𝐧𝐠 𝐔𝐬𝐞 𝐎𝐫𝐢𝐠𝐢𝐧𝐚𝐥 𝐛𝐨𝐭 ↓", reply_markup=btn)
    
    # Permission check: Only Admin/Owner can clone
    if not (message.from_user.id in OWNERS or client.bot_db.is_admin(message.from_user.id)):
        return await message.reply(LOYAL_MSG, parse_mode=enums.ParseMode.HTML)

    if len(message.command) < 2:
        return await message.reply("⚠️ Please provide a bot token. Example: `/clone 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` ")    
    token = message.command[1]
    msg = await message.reply("⏳ Cloning your bot, please wait...")
    
    try:
        new_clone = FileStoreBot(
            name=f"clone_{token.split(':')[0]}", 
            bot_token=token, 
            api_id=API_ID, 
            api_hash=API_HASH, 
            plugins=None,
            in_memory=True
        )
        new_clone.is_clone = True
        new_clone.clone_owner = message.from_user.id
        await new_clone.start()
        
        for group, handlers in bot.dispatcher.groups.items():
            for handler in handlers:
                new_clone.add_handler(handler, group)
                
        bot_info = await new_clone.get_me()
        client.bot_db.add_clone(bot_info.id, token, message.from_user.id)
        active_clones.append(new_clone)
        
        user_full_name = message.from_user.first_name
        owner_id_str = str(message.from_user.id)
        bot_id_str = str(bot_info.id)
        
        text = (
            f"✅ **Bᴏᴛ Cʟᴏɴᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n\n"
            f"🤖 **Bᴏᴛ Nᴀᴍᴇ:** {bot_info.first_name}\n"
            f"🔗 **Uꜱᴇʀɴᴀᴍᴇ:** @{bot_info.username}\n\n"
            f"👤 **User who cloned:** [{user_full_name}](tg://openmessage?user_id={owner_id_str})"
        )
        
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("𝚁𝚎𝚖𝚘𝚟𝚎 𝚝𝚑𝚒𝚜 𝚌𝚕𝚘𝚗𝚎 𝚋𝚘𝚝", callback_data=f"rm_clone_{bot_id_str}")
        ]])
        
        await msg.edit(text, reply_markup=btn)
    except BaseException as e:
        try: await new_clone.stop()
        except: pass
        await msg.edit(f"❌ Failed to clone bot: {e}")

@bot.on_message(ban_filter & filters.command("clone_list") & filters.private)
async def clone_list_cmd(client, message: Message):
    # --- CLONE BOT RESTRICTION ---
    if getattr(client, "is_clone", False):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("𝗭𝗨𝗜𝗜 𝗕𝗢𝗧", url=f"https://t.me/{MAIN_BOT_USERNAME}")]])
        return await message.reply("↓ 𝐅𝐨𝐫 𝐂𝐥𝐨𝐧𝐞 𝐋𝐢𝐬𝐭 𝐔𝐬𝐞 𝐎𝐫𝐢𝐠𝐢𝐧𝐚𝐥 𝐛𝐨𝐭 ↓", reply_markup=btn)

    # --- ADMIN/OWNER PERMISSION CHECK ---
    if not (message.from_user.id in OWNERS or client.bot_db.is_admin(message.from_user.id)):
        return await message.reply(LOYAL_MSG, parse_mode=enums.ParseMode.HTML)

    # --- ORIGINAL LOGIC (REST OF THE FEATURES) ---
    clones = client.bot_db.get_all_clones()
    if not clones: 
        return await message.reply("🤖 **Koi bhi clone bot active nahi hai.**")
    
    status_msg = await message.reply("⏳ **Fetching Active Clones...**")
    
    for c in clones:
        owner_id_str = str(c["owner_id"])
        bot_id_str = str(c["bot_id"])
        
        try:
            user = await client.get_users(int(owner_id_str))
            user_full_name = f"{user.first_name} {user.last_name or ''}".strip()
        except:
            user_full_name = "Unknown User"

        bot_name = "Unknown Bot"
        bot_username = "Unknown"
        
        for clone_client in active_clones:
            if hasattr(clone_client, 'bot_token') and bot_id_str in clone_client.bot_token:
                try:
                    bot_info = await clone_client.get_me()
                    bot_name = bot_info.first_name
                    bot_username = bot_info.username
                except:
                    pass
                break
                
        text = (
            f"✅ **Aᴄᴛɪᴠᴇ Cʟᴏɴᴇ Bᴏᴛ!**\n\n"
            f"🤖 **Bᴏᴛ Nᴀᴍᴇ:** {bot_name}\n"
            f"🔗 **Uꜱᴇʀɴᴀᴍᴇ:** @{bot_username}\n\n"
            f"👤 **User who cloned:** [{user_full_name}](tg://openmessage?user_id={owner_id_str})"
        )
        
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("𝚁𝚎𝚖𝚘𝚟𝚎 𝚝𝚑𝚒𝚜 𝚌𝚕𝚘𝚗𝚎 𝚋𝚘𝚝", callback_data=f"rm_clone_{bot_id_str}")
        ]])
        
        await message.reply(text, reply_markup=btn, disable_web_page_preview=True)
        await asyncio.sleep(0.3)

    await status_msg.delete()


@bot.on_callback_query(filters.regex(r"^rm_clone_"))
async def remove_clone_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    clones = client.bot_db.get_all_clones()
    clone_data = next((c for c in clones if c["bot_id"] == bot_id), None)
    
    if not clone_data:
        return await query.answer("⚠️ Ye clone pehle hi remove ho chuka hai ya nahi mila.", show_alert=True)
        
    # SECURITY: Check if the person clicking is the OWNER of the bot, or the Main Bot Admin
    if not (user_id in OWNERS or client.bot_db.is_admin(user_id) or user_id == clone_data["owner_id"]):
        return await query.answer("❌ Aap is clone ko remove karne ke liye authorized nahi hain.", show_alert=True)

    # Stop Client properly to release connection
    for clone_client in active_clones[:]:
        if hasattr(clone_client, 'bot_token') and str(bot_id) in clone_client.bot_token:
            try: 
                await clone_client.stop()
            except: 
                pass
            active_clones.remove(clone_client)
            
    # Remove from Database
    client.bot_db.clones.delete_one({"bot_id": bot_id})
    
    await query.message.edit_text("🗑 **Ye Clone bot successfully remove aur disconnect kar diya gaya hai.**")


@bot.on_message(ban_filter & filters.command("stop") & filters.private)
async def stop_user_clone(client, message: Message):
    # --- CLONE BOT RESTRICTION ---
    if getattr(client, "is_clone", False):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("𝗭𝗨𝗜𝗜 𝗕𝗢𝗧", url=f"https://t.me/{MAIN_BOT_USERNAME}")]])
        return await message.reply("↓ 𝐅𝐨𝐫 𝐒𝐭𝐨𝐩𝐩𝐢𝐧𝐠 𝐂𝐥𝐨𝐧𝐞 𝐔𝐬𝐞 𝐎𝐫𝐢𝐠𝐢𝐧𝐚𝐥 𝐛𝐨𝐭 ↓", reply_markup=btn)

    # --- ORIGINAL LOGIC (STOPPING FEATURES) ---
    user_id = message.from_user.id
    clones = client.bot_db.get_all_clones()
    user_clones = [c for c in clones if c["owner_id"] == user_id]
    
    if not user_clones:
        return await message.reply("⚠️ **Aapka koi bhi clone bot active nahi hai.**")
        
    for c in user_clones:
        bot_id = c["bot_id"]
        
        for clone_client in active_clones[:]:
            if hasattr(clone_client, 'bot_token') and str(bot_id) in clone_client.bot_token:
                try: 
                    await clone_client.stop()
                except Exception as e: 
                    logger.error(f"Error stopping clone {bot_id}: {e}")
                if clone_client in active_clones:
                    active_clones.remove(clone_client)
                
        client.bot_db.clones.delete_one({"bot_id": bot_id})
        
    await message.reply("✅ **Aapka Clone Bot successfully disconnect aur stop kar diya gaya hai.**")

#============= Stats (FINAL PREMIUM UI) ==============
@bot.on_message(ban_filter & filters.command("stats") & is_admin & filters.private)
async def stats_handler(client, message: Message):
    try:
        stats = client.bot_db.get_stats_counts()
        stats_text = (
            "<b>🕊️❀Bᴏᴛ Sᴛᴀᴛᴜs ❁</b>\n"
            "<b>╭────────────────⟢</b>\n"
            f"<b>│ ✦ Wʜɪᴛᴇ Usᴇʀs: {stats['white_users']:03}</b>\n"
            f"<b>│ ⛨ Fᴏʀᴄᴇsᴜʙ : {stats['forcesub']:03}</b>\n"
            f"<b>│ ✧ Bʟᴏᴄᴋ Usᴇʀs : {stats['block_users']:03}</b>\n"
            f"<b>│ ⌬ Tᴏᴛᴀʟ Usᴇʀs : {stats['total_users']:03}</b>\n"
            "<b>╰────────────────⟢</b>"
        )
        await message.reply(stats_text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Stats Error: {e}")
        await message.reply(f"<b>❌ Error:</b>\n<code>{e}</code>", parse_mode=enums.ParseMode.HTML)

async def auto_delete_task(client, chat_id: int, message_ids: List[int], delay: int):
    await asyncio.sleep(delay)
    try: await client.delete_messages(chat_id, message_ids)
    except Exception as e: logger.error(f"Auto-delete failed: {e}")

# --- SHORTENER SETTINGS HANDLERS ---
@bot.on_message(ban_filter & filters.command("linkshortner") & is_admin & filters.private)
async def shortner_settings_handler(client, message: Message):
    config1 = client.bot_db.get_shortener_config(1)
    config2 = client.bot_db.get_shortener_config(2)
    
    active1 = client.bot_db.get_setting("SHORTENER_1_ACTIVE", "1") == "1"
    active2 = client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "1"
    
    text = "✦ **𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦**\n\n"
    text += "**ᴄᴜʀʀᴇɴᴛ ꜱᴇᴛᴛɪŋɢꜱ:**\n\n"
    
    text += "**𝟭. ━━━━━━━━━━━━━━━━━━**\n"
    text += f"›› <b>ꜱʜᴏʀᴛɴᴇʀ ᴜʀʟ:</b> `{config1.get('url') or 'Not Configured'}`\n"
    text += f"›› <b>Ref ᴀᴘɪ:</b> `{config1.get('api') or 'Not Configured'}`\n"
    text += f"›› <b>ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ:</b> `{config1.get('tut') or 'Not Configured'}`\n"
    text += f"›› <b><b>ʙʏᴘᴀꜱꜱ ᴛɪᴍᴇ:</b> `{config1.get('time', 65)} sec`\n\n"
    
    has_custom_shortener = False
    is_slot1_default = config1.get("is_default") or (config1.get("api") == SHORTENER_API and config1.get("url") == SHORTENER_URL)
    
    if not is_slot1_default:
        has_custom_shortener = True
    
    if config2.get("api"):
        has_custom_shortener = True
        text += "**𝟮. ━━━━━━━━━━━━━━━━━━**\n"
        text += f"›› <b>ꜱʜᴏʀᴛɴᴇʀ ᴜʀʟ:</b> `{config2.get('url')}`\n"
        text += f"›› <b>ꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ:</b> `{config2.get('api')}`\n"
        text += f"›› <b>ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ:</b> `{config2.get('tut')}`\n"
        text += f"›› <b>ʙʏᴘᴀꜱꜱ ᴛɪᴍᴇ:</b> `{config2.get('time', 65)} sec`\n\n"
    else:
        text += "**𝟮. ━━━━━━━━━━━━━━━━━━**\n**Slot Empty (Click Add Shortener below to populate)**\n\n"
        
    text += "≡ ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴꜰɪɢᴜʀᴇ ʏᴏᴜʀ ꜱʜᴏʀᴛɴᴇʀ ꜱᴇᴛᴛɪɴɢꜱ!"

    keyboard = []
    
    if config2.get("api"):
        btn1_label = f"Shortener 1 {'✅' if active1 else '❌'}"
        btn2_label = f"Shortener 2 {'✅' if active2 else '❌'}"
        keyboard.append([
            InlineKeyboardButton(btn1_label, callback_data="toggle_act_1"),
            InlineKeyboardButton(btn2_label, callback_data="toggle_act_2")
        ])
        
    # FIX: Add button rendering fallback matrix validation check
    if is_slot1_default or not config2.get("api"):
        keyboard.append([InlineKeyboardButton("• ᴀᴅᴅ ꜱʜᴏʀᴛɴᴇʀ •", callback_data="submenu_add")])
        
    if has_custom_shortener:
        keyboard.append([InlineKeyboardButton("• ʀᴇᴍ ꜱʜᴏʀᴛɴᴇʀ •", callback_data="submenu_rem")])
        
    keyboard.append([InlineKeyboardButton("• ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ •", callback_data="submenu_tut")])
    keyboard.append([InlineKeyboardButton("• ʙʏᴘᴀꜱꜱ ᴛɪᴍᴇ •", callback_data="submenu_time")])

    await message.reply_photo(
        photo=client.bot_db.get_bot_img(client.me.id, IMG_URL),
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



@bot.on_callback_query(filters.regex(r"^(submenu_|toggle_|confirm_|remove_active_|execute_|main_shortener_refresh|input_trigger_)"))
async def upgrade_shortener_callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    config1 = client.bot_db.get_shortener_config(1)
    config2 = client.bot_db.get_shortener_config(2)
    
    # Main Refresh Menu Interface Logic (Fixes Back Buttons crashing/not working)
    if data == "main_shortener_refresh":
        await query.answer("Navigating Back...")
        return await refresh_shortener_interface(client, query.message)

    # --- ACTIVE STATE STATUS ROTATING SWITCH CONTROLLERS ---
    if data.startswith("toggle_act_"):
        target_idx = int(data.split("_")[2])
        if target_idx == 1:
            curr_state = client.bot_db.get_setting("SHORTENER_1_ACTIVE", "1") == "1"
            new_state = "0" if curr_state else "1"
            if new_state == "0" and client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "0":
                return await query.answer("⚠️ System alert! Dono shorteners ko band nahi kiya ja sakta.", show_alert=True)
            
            confirm_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes, Confirm Switch", callback_data=f"execute_toggle_1_{new_state}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="main_shortener_refresh")]
            ])
            return await query.message.edit_reply_markup(reply_markup=confirm_kb)
            
        elif target_idx == 2:
            curr_state = client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "1"
            new_state = "0" if curr_state else "1"
            if new_state == "0" and client.bot_db.get_setting("SHORTENER_1_ACTIVE", "1") == "0":
                return await query.answer("⚠️ System alert! Dono shorteners ko band nahi kiya ja sakta.", show_alert=True)
                
            confirm_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes, Confirm Switch", callback_data=f"execute_toggle_2_{new_state}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="main_shortener_refresh")]
            ])
            return await query.message.edit_reply_markup(reply_markup=confirm_kb)

    if data.startswith("execute_toggle_"):
        parts = data.split("_")
        idx = parts[2]
        state_val = parts[3]
        client.bot_db.set_setting(f"SHORTENER_{idx}_ACTIVE", state_val)
        await query.answer("🔄 Activation matrix modified updated!")
        return await refresh_shortener_interface(client, query.message)

    # --- SUBMENU CONTROLS ROUTER PATH ---
    if data == "submenu_add":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm and Continue ➡️", callback_data="confirm_add_trigger")],
            [InlineKeyboardButton("Back 🔙", callback_data="main_shortener_refresh")]
        ])
        await query.message.edit_reply_markup(reply_markup=kb)
        
    elif data == "confirm_add_trigger":
        # Check if Slot 1 still holds the default environment configuration
        is_slot1_default = (config1.get("api") == SHORTENER_API and config1.get("url") == SHORTENER_URL)
        
        # Decide the target slot based on user custom preference mapping
        if is_slot1_default:
            slot = 1  # Re-route to Slot 1 to overwrite default global system keys
        elif not config2.get("api"):
            slot = 2  # Route to empty Slot 2 if Slot 1 already has custom credentials
        else:
            return await query.answer("⚠️ Dono Shortener Slots pehle se full hain! Pehle koi ek remove karein.", show_alert=True)
            
        await query.message.edit_text(
            f"🔗 **[Slot {slot}] Please send your Shortener API URL.**\n"
            f"Example: `https://arolinks.com/api` \n\n"
            f"Type the link or send `/cancel` to abort."
        )
        client.collecting_users[user_id] = {"mode": "setting_url", "target_slot": slot}

    # --- REMOVE ROUTER PIPELINE ARCHITECTURE ---
    elif data == "submenu_rem":
        # Ensure user can only wipe custom defined configuration indices
        if config1.get("api") and config2.get("api"):
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("ꜱʜᴏʀᴛɴᴇʀ 𝟭", callback_data="remove_active_1"),
                 InlineKeyboardButton("ꜱʜᴏʀᴛɴᴇʀ 𝟮", callback_data="remove_active_2")],
                [InlineKeyboardButton("Back 🔙", callback_data="main_shortener_refresh")]
            ])
            await query.message.edit_reply_markup(reply_markup=kb)
        else:
            target_slot = 1 if (config1.get("api") and config1.get("api") != SHORTENER_API) else 2
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚠️ Click to Double Confirm Wipe", callback_data=f"execute_wipe_{target_slot}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="main_shortener_refresh")]
            ])
            await query.message.edit_reply_markup(reply_markup=kb)

    elif data.startswith("remove_active_"):
        slot = data.split("_")[2]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⚠️ Confirm Destruction Slot {slot}?", callback_data=f"execute_wipe_{slot}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="main_shortener_refresh")]
        ])
        await query.message.edit_reply_markup(reply_markup=kb)

    elif data.startswith("execute_wipe_"):
        slot = int(data.split("_")[2])
        if slot == 1:
            # Revert Slot 1 to default and mark it explicitly as clean default state
            client.bot_db.set_shortener_config(1, {
                "url": SHORTENER_URL, 
                "api": SHORTENER_API, 
                "tut": TUTORIAL_LINK, 
                "time": BYPASS_TIME_LIMIT,
                "is_default": True # 👈 Indicator checking matrix binding
            })
            client.bot_db.set_setting("SHORTENER_1_ACTIVE", "1")
        else:
            client.bot_db.set_shortener_config(2, {"url": "", "api": "", "tut": "", "time": 65})
            client.bot_db.set_setting("SHORTENER_2_ACTIVE", "0")
            client.bot_db.set_setting("SHORTENER_1_ACTIVE", "1")
            
        await query.answer("🗑️ Shortener asset layer completely reset successfully!")
        return await refresh_shortener_interface(client, query.message)

    # --- TUTORIAL & TIME TARGET SELECTION HANDLERS ---
    elif data in ["submenu_tut", "submenu_time"]:
        action_type = "tut" if "tut" in data else "time"
        if config2.get("api"):
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("• ꜱʜᴏʀᴛɴᴇʀ 𝟭 •", callback_data=f"input_trigger_1_{action_type}"),
                 InlineKeyboardButton("• ꜱʜᴏʀᴛɴᴇʀ 𝟮 •", callback_data=f"input_trigger_2_{action_type}")],
                [InlineKeyboardButton("Back 🔙", callback_data="main_shortener_refresh")]
            ])
            await query.message.edit_reply_markup(reply_markup=kb)
        else:
            # Directly target Slot 1 with instant fallback edit mechanics
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("Back 🔙", callback_data="main_shortener_refresh")]])
            await query.message.edit_text(f"📘 **Enter context asset updates for Shortener 1.**\nType target string parameter updates or send `/cancel`.", reply_markup=kb)
            client.collecting_users[user_id] = {"mode": f"setting_{action_type}", "target_slot": 1}

    elif data.startswith("input_trigger_"):
        slot = int(data.split("_")[2])
        act = data.split("_")[3]
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Back 🔙", callback_data="main_shortener_refresh")]])
        await query.message.edit_text(f"📥 **[Slot {slot}] Input parameter value data stream initialization layer active...**\nType values update parameter data assets or /cancel.", reply_markup=kb)
        client.collecting_users[user_id] = {"mode": f"setting_{act}", "target_slot": slot}


# Interface rendering orchestration layout manager routine function helper
async def refresh_shortener_interface(client, existing_message):
    config1 = client.bot_db.get_shortener_config(1)
    config2 = client.bot_db.get_shortener_config(2)
    active1 = client.bot_db.get_setting("SHORTENER_1_ACTIVE", "1") == "1"
    active2 = client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "1"
    
    text = "✦ **𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦**\n\n"
    text += "<b>ᴄᴜʀʀᴇŋᴛ ꜱᴇᴛᴛɪŋɢ:</b>\n\n"
    text += "**𝟭. ━━━━━━━━━━━━━━━━━━**\n"
    text += f"<b>›› ꜱʜᴏʀᴛɴᴇʀ ᴜʀʟ:</b> `{config1.get('url') or 'Not Configured'}`\n"
    text += f"<b>›› ꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ:</b>`{config1.get('api') or 'Not Configured'}`\n"
    text += f"<b>›› ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ:</b> `{config1.get('tut') or 'Not Configured'}`\n"
    text += f"<b>›› ʙʏᴘᴀꜱꜱ ᴛɪᴍᴇ:</b> `{config1.get('time', 65)} sec`\n\n"
    
    has_custom_shortener = False
    is_slot1_default = config1.get("is_default") or (config1.get("api") == SHORTENER_API and config1.get("url") == SHORTENER_URL)
    
    if not is_slot1_default:
        has_custom_shortener = True

    if config2.get("api"):
        has_custom_shortener = True
        text += "**𝟮. ━━━━━━━━━━━━━━━━━━**\n"
        text += f"<b>›› ꜱʜᴏʀᴛɴᴇʀ ᴜʀʟ: </b>`{config2.get('url')}`\n"
        text += f"<b>›› ꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ:</b> `{config2.get('api')}`\n"
        text += f"<b>›› ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ:</b> `{config2.get('tut')}`\n"
        text += f"<b>›› ʙʏᴘᴀꜱ𝖘 ᴛɪᴍᴇ:</b>`{config2.get('time', 65)} sec`\n\n"
    else:
        text += "**𝟮. ━━━━━━━━━━━━━━━━━━**\n<b>Slot Empty (Click Add Shortener below to populate)</b>\n\n"
        
    text += "≡ ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴꜰɪɢᴜʀᴇ ʏᴏᴜʀ ꜱʜᴏʀᴛɴᴇʀ ꜱᴇᴛᴛɪɴɢꜱ!"

    keyboard = []
    if config2.get("api"):
        btn1_label = f"Shortener 1 {'✅' if active1 else '❌'}"
        btn2_label = f"Shortener 2 {'✅' if active2 else '❌'}"
        keyboard.append([InlineKeyboardButton(btn1_label, callback_data="toggle_act_1"), InlineKeyboardButton(btn2_label, callback_data="toggle_act_2")])
        
    # Verification condition alignment optimized for slot restoration pipelines
    if is_slot1_default or not config2.get("api"):
        keyboard.append([InlineKeyboardButton("• ᴀᴅᴅ ꜱʜᴏʀᴛɴᴇʀ •", callback_data="submenu_add")])
        
    if has_custom_shortener:
        keyboard.append([InlineKeyboardButton("• ʀᴇᴍ ꜱʜᴏʀᴛɴᴇʀ •", callback_data="submenu_rem")])
        
    keyboard.append([InlineKeyboardButton("• ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ •", callback_data="submenu_tut")])
    keyboard.append([InlineKeyboardButton("• ʙʏᴘᴀꜱꜱ ᴛɪᴍᴇ •", callback_data="submenu_time")])
    
    try:
        await existing_message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        try:
            await existing_message.edit_caption(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Menu refresh failed: {e}")

            

# --- MASTER COMBINED INPUT LISTENER (FIXED FILTER MATRIX) ---
@bot.on_message(ban_filter & filters.private, group=-1) 
async def master_input_listener(client, message: Message):
    user_id = message.from_user.id
    bot_id = client.me.id
    
    # Allow target structural dashboard text escape routes cleanly
    if message.text and message.text.startswith("/"):
        if message.text.split()[0].lower() not in ["/cancel"]:
            raise ContinuePropagation

    # 1. SPECIAL CHECK FOR CUSTOMIZATION SYSTEM SESSIONS
    if user_id in customize_sessions:
        session = customize_sessions[user_id]
        mode = session.get("mode", "main_menu")
        
        if mode == "main_menu" or not mode.startswith("wait_"):
            raise ContinuePropagation

        target_key = mode.replace("wait_", "").upper()
        
        # FIX: Key mismatch resolver for start handler
        if target_key == "START":
            target_key = "START_CAPTION"
        
        # Capture raw html context to perfectly retain custom user font variations
        raw_html_input = message.text.html if message.text else ""

        if not raw_html_input and message.caption:
            raw_html_input = message.caption.html

        if not raw_html_input and message.text:
            raw_html_input = html.escape(message.text)

        if not raw_html_input:
            return await message.reply("❌ **Please send a text message with proper formatting styles (bold, italic, links etc).**")

        # Dynamic placeholder mapping controls
        if target_key == "AUTODEL" and "{readable}" not in raw_html_input:
            raw_html_input = "⏱️ {readable}\n\n" + raw_html_input
            
        if target_key == "FORCESUB":
            prefix = "Hᴇʟʟᴏ Dᴇᴀʀ {message.from_user.first_name}\n\n"
            if "{message.from_user.first_name}" not in raw_html_input:
                raw_html_input = prefix + raw_html_input

        # Handle Immediate data storage bindings (No confirmation preview window needed)
        if target_key == "BTN_NAME":
            client.bot_db.set_custom_msg(bot_id, "BTN_NAME", message.text.strip())
            await message.reply("✅ **Button text name modified update saved successfully!**")
            return await restore_dashboard_view(client, user_id, session["msg_id"], message.chat.id)

        if target_key == "BTN_LINK":
            link_text = message.text.strip()
            if not link_text.startswith("http"):
                return await message.reply("❌ **Invalid link format! Target URL must start with http:// or https://**")
            client.bot_db.set_custom_msg(bot_id, "BTN_LINK", link_text)
            await message.reply("✅ **Button target endpoint link destination configured securely!**")
            return await restore_dashboard_view(client, user_id, session["msg_id"], message.chat.id)

        # Cache text structures for dynamic verification display
        session["text"] = raw_html_input
        session["timestamp"] = time.time()
        
        try: await message.delete()
        except: pass

        preview_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✔️ Confirm and Save Layout", callback_data=f"cust_save_{target_key}")],
            [InlineKeyboardButton("❌ Discard & Back", callback_data="cust_back_main")]
        ])

        try:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=session["msg_id"],
                text=f"👁️‍🗨️ **PREVIEW RENDER LOOKOUT LAYER:**\n\n{raw_html_input}\n\n━━━━━━━━━━━━━━━━━━━━\n✨ *Verify rendering components properties alignment below:*",
                reply_markup=preview_keyboard
            )
        except Exception as err:
            await client.send_message(message.chat.id, f"❌ **Rendering Matrix Error:** `{err}`\nTry running basic text formatting layout rules.")
        return

    # 2. CHECK FOR SHORTENER DUAL SETTINGS COLLECTOR LAYER
    if user_id in client.collecting_users:
        state = client.collecting_users[user_id]
        mode = state.get("mode")
        slot = state.get("target_slot", 1)
        
        if mode in ["setting_url", "setting_token", "setting_tut", "setting_time"]:
            current_config = client.bot_db.get_shortener_config(slot)
            
            if mode == "setting_url":
                url = message.text.strip()
                if not url.startswith("http"): 
                    await message.reply("❌ Invalid URL! Please send a proper link.")
                    return  # 👈 Fixed leak
                state["temp_url"] = url
                state["mode"] = "setting_token"
                await message.reply(f"✅ URL Saved inside Slot {slot}: `{url}`\n\n🔑 Now, please send your **API Token/Key**.")
                return  # 👈 Fixed leak
                
            elif mode == "setting_token":
                api_key = message.text.strip()
                url = state.get("temp_url")
                current_config["url"] = url
                current_config["api"] = api_key
                if slot == 1 and "is_default" in current_config:
                    current_config.pop("is_default")
                client.bot_db.set_shortener_config(slot, current_config)
                client.collecting_users.pop(user_id) 
                await message.reply(f"✅ **Slot {slot} Updated Success!**\n\nURL: `{url}`\nAPI: `{api_key}`")
                return  # 👈 Fixed leak
                
            elif mode == "setting_tut":
                tut_url = message.text.strip()
                if not tut_url.startswith("http"): 
                    await message.reply("❌ Invalid Link!")
                    return  # 👈 Fixed leak
                current_config["tut"] = tut_url
                client.bot_db.set_shortener_config(slot, current_config)
                client.collecting_users.pop(user_id)
                await message.reply(f"✅ **Slot {slot} Success!**\n\nTutorial link updated to: `{tut_url}`")
                return  # 👈 Fixed leak
                
            elif mode == "setting_time":
                time_limit = message.text.strip()
                if not time_limit.isdigit(): 
                    await message.reply("❌ Invalid Input! Numbers only.")
                    return  # 👈 Fixed leak
                current_config["time"] = int(time_limit)
                client.bot_db.set_shortener_config(slot, current_config)
                client.collecting_users.pop(user_id)
                await message.reply(f"✅ **Slot {slot} Success!**\n\nBypass time limit updated to: `{time_limit} seconds`")
                return  # 👈 Fixed leak

        # Catch-all termination handler for linkshortener input mode
        return 

    raise ContinuePropagation






# --- HELPER FUNCTION TO SAFELY RESTORE DASHBOARD MATRIX ---
async def restore_dashboard_view(client, user_id, msg_id, chat_id):
    if user_id in customize_sessions:
        customize_sessions[user_id]["mode"] = "main_menu"
    text, markup = get_customize_menu()
    try:
        await client.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text, reply_markup=markup)
    except:
        pass
        
@bot.on_message(ban_filter & filters.command("cancel") & filters.private)
async def cancel_process_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id in client.collecting_users:
        client.collecting_users.pop(user_id)
        await message.reply("❌ **Process cancelled.** All pending actions have been cleared.")
    else:
        await message.reply("No active process to cancel.")
        
@bot.on_message(ban_filter & filters.command("help") & filters.private)
async def help_cmd(client, message: Message):
    text = "👋 **Welcome to File Store Bot**\n\n"
    is_admin_check = message.from_user.id in OWNERS or client.bot_db.is_admin(message.from_user.id) or (getattr(client, "is_clone", False) and getattr(client, "clone_owner", None) == message.from_user.id)
    if is_admin_check:
        text += (
            "**Admin Commands:**\n"
            "/file - Start batch collection\n"
            "/link - Create Linkshortner Botlink\n"
            "/end - Finish batch collection\n"
            "/linkshortner - Set Costom linkshortner\n"
            "/Show_links - Show All Bot link\n"
            "/Broadcast - Broadcast Message to All User\n"
            "/rm - Remove Botlink And File\n"
            "/forcesub - Manage join requirements\n"
            "/remove - Remove ForceSub channel\n"
            "/on - Enable content protection\n"
            "/off - Disable content protection\n"
            "/time - Set auto-delete timer\n"
            "/back_up - Get DB backup\n"
            "/restore - Restore from backup\n"
            "/db - Export & wipe MongoDB database\n"
            "/ban - Ban a user\n"
            "/unban - Unban a user\n"
            "/ban_list - To View All Ban User\n" 
            "/add_pri {User_id/Username} To Add user in Primium list\n"
            "/rem_pri {User_id/Username} To Rem User From Primium List\n" 
            "/pri_list to View All PRIMIUM User\n" 
            "/add_admin - Add admin (Owners only)\n"
            "/remove_admin - Remove admin (Owners only)\n"
            "/admin_list - View admins\n"
            "/clone - Clone this bot\n"
            "/clone_list - View clones\n"
            "/st - Set Dynamic Storage Channel\n"
            "/img reply image to set bot thumbnail or see current\n" 
            "/img remove to back to default bot thambnail\n"
            "/customize to customize  own bot msg\n"
        )
    else: text += "Send me a valid link to get your files."
    await message.reply(text)

@bot.on_message(ban_filter & filters.command("link") & is_admin & filters.private)    
async def start_link_collection(client, message: Message):    
    if not get_storage_id(client):
        return await message.reply("⚠️ **Pehle apna storage channel set karein!**\nUse `/st <channel_id>` to set it.")
        
    user_id = message.from_user.id    
    session_id = str(uuid.uuid4())[:8]    
    client.collecting_users[user_id] = {"id": session_id, "messages": [], "mode": "link"}    
    await message.reply(    
    f"""**🌸 ꜱᴛᴀʀᴛᴇᴅ ᴄᴏʟʟᴇᴄᴛɪɴɢ ꜰɪʟᴇꜱ🌻    \nɢʀᴏᴜᴘ ɪᴅ: {session_id} 💌** \n**ᴀʙ ᴀᴀᴘ ᴀᴘɴɪ ꜱᴀᴀʀɪ ᴍᴇᴅɪᴀ ʙʜᴇᴊ ꜱᴀᴋᴛᴇ ʜᴏ ✨** \n**ᴊᴀʙ ᴋᴀᴀᴍ ᴘᴜʀᴀ ʜᴏ ᴊᴀʏᴇ ᴛᴏ /end ᴜꜱᴇ ᴋᴀʀ ᴅᴇɴᴀ 💞**"""    
)
    
@bot.on_message(ban_filter & filters.command("file") & is_admin & filters.private)    
async def start_file_collection(client, message: Message):    
    if not get_storage_id(client):
        return await message.reply("⚠️ **Pehle apna storage channel set karein!**\nUse `/st <channel_id>` to set it.")
        
    user_id = message.from_user.id    
    session_id = str(uuid.uuid4())[:8]    
    client.collecting_users[user_id] = {"id": session_id, "messages": [], "mode": "file"}    
    await message.reply(    
    f"""**🌸 ꜱᴛᴀʀᴛᴇᴅ ᴄᴏʟʟᴇᴄᴛɪɴɢ ꜰɪʟᴇꜱ🌻    \nɢʀᴏᴜᴘ ɪᴅ: {session_id} 💌** \n**ᴀʙ ᴀᴀᴘ ᴀᴘɴɪ ꜱᴀᴀʀɪ ᴍᴇᴅɪᴀ ʙʜᴇᴊ ꜱᴀᴋᴛᴇ ʜᴏ ✨** \n**ᴊᴀʙ ᴋᴀᴀᴍ ᴘᴜʀᴀ ʜᴏ ᴊᴀʏᴇ ᴛᴏ /end ᴜꜱᴇ ᴋᴀʀ ᴅᴇɴᴀ 💞**"""    
)

@bot.on_message(ban_filter & filters.command("end") & is_admin & filters.private)
async def end_file_collection(client, message: Message):
    user_id = message.from_user.id
    if user_id not in client.collecting_users: return await message.reply("You aren't collecting any files!")
    data = client.collecting_users.pop(user_id)
    if not data["messages"]: return await message.reply("**ᴀʙʜɪ ᴛᴀᴋ ᴋᴏɪ ʙʜɪ ꜰɪʟᴇ ᴄᴏʟʟᴇᴄᴛ ɴᴀʜɪ.**")
    
    unique_id = data["id"]
    protect = client.bot_db.get_setting("protect_content", "0") == "1"
    mode = data.get("mode", "file")

    client.bot_db.add_batch(unique_id, data["messages"], protect, link_mode=(1 if mode == "link" else 0))
    link = f"https://t.me/{client.me.username}?start={unique_id}"
    
    if mode == "link": msg_text = f"✅ **🎉 ʟɪɴᴋꜱʜᴏʀᴛɴᴇʀ ʙᴀᴛᴄʜ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ 💞!**\n\n🔗 {link}"
    else: msg_text = f"✅ **🎉 ʙᴀᴛᴄʜ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ 💞!**\n\n🔗 {link}"
    await message.reply(msg_text, disable_web_page_preview=True)
    
@bot.on_message(ban_filter & filters.command("forcesub") & is_admin & filters.private)
async def add_forcesub_cmd(client, message: Message):
    # DAFFA 1: Upgraded List Routing (Separate Messages, 1-Hour Temp Links & 1-Hour Auto Delete)
    if len(message.command) > 1 and message.command[1].lower() == "list":
        channels = client.bot_db.get_all_forcesub()
        if not channels:
            return await message.reply("📡 <b>Forcesub Cluster Registry:</b> <code>Clean (No limits set)</code>")
        
        status_card = await message.reply("⏳ <b>Polling real-time database cluster information blocks...</b>")
        sent_message_ids = []

        for idx, chat_id in enumerate(channels, start=1):
            try:
                chat = await client.get_chat(chat_id)
                title = chat.title
                members_count = chat.members_count
                username = f"@{chat.username}" if chat.username else "Private Gateway"
                
                # Strict 1-Hour Temporary Invite Link Generation (No Join Request)
                try:
                    temp_link_obj = await client.create_chat_invite_link(
                        chat_id=chat_id, 
                        expire_date=datetime.now() + timedelta(hours=1), 
                        creates_join_request=False  # 👈 Join request disabled
                    )
                    invite_link = temp_link_obj.invite_link
                    link_status = "⏱️ Temporary (Expires in 1 hour)"
                    
                    # Separate Message layout card for each node
                    report_output = (
                        f"🛰️ <b>𝗙𝗢𝗥𝗖𝗘𝗦𝗨𝗕 𝗟𝗜𝗡𝗞 𝗡𝗢𝗗𝗘 [{idx:02d}]</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📡 <b>Cluster Status:</b> <code>Active Grid</code>\n"
                        f"🏷️ <b>Channel Name:</b> <code>{html.escape(title)}</code>\n"
                        f"🆔 <b>Target ID:</b> <code>{chat_id}</code>\n"
                        f"👥 <b>Core Load:</b> <code>{members_count} Members</code>\n"
                        f"🔗 <b>Handle:</b> {username}\n"
                        f"🔐 <b>Link Type:</b> <i>{link_status}</i>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🌐 <b>Direct Portal:</b> <a href='{invite_link}'>Click to See Channel</a>\n\n"
                        f"⏱️ <i>This card and link will self-destruct in 1 hour.</i>"
                    )
                    
                    single_msg = await message.reply(report_output, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                    sent_message_ids.append(single_msg.id)
                    await asyncio.sleep(0.4) # FloodWait mitigation delay
                    
                except Exception as link_err:
                    logger.error(f"Failed to generate 1-hour temp link for {chat_id}: {link_err}")
                    # Error aane par permanent link show karne ke bajaye seedhe crash alert card dega
                    fault_card = (
                        f"⚠️ <b>𝗟𝗜𝗡𝗞 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗜𝗢𝗡 𝗙𝗔𝗜𝗟𝗘𝗗 [{idx:02d}]</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 <b>Channel ID:</b> <code>{chat_id}</code>\n"
                        f"❌ <b>Reason:</b> <i>Bot ke paas unique invite link generate karne ki permission nahi hai.</i>\n"
                        f"💡 <b>Fix:</b> Channel Admin settings mein jaakar bot ko <b>'Invite Users via Link'</b> ki permission dein.\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    single_msg = await message.reply(fault_card, parse_mode=enums.ParseMode.HTML)
                    sent_message_ids.append(single_msg.id)

            except Exception as cluster_err:
                fault_card = (
                    f"⚠️ <b>𝗡𝗢𝗗𝗘 𝗙𝗔𝗨𝗟𝗧 𝗘𝗥𝗥𝗢𝗥 [{idx:02d}]</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 <b>Channel ID:</b> <code>{chat_id}</code>\n"
                    f"❌ <b>Diagnostic Trace:</b> <i>{cluster_err}</i>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                single_msg = await message.reply(fault_card, parse_mode=enums.ParseMode.HTML)
                sent_message_ids.append(single_msg.id)

        # Clean up the initial loading status card
        try:
            await status_card.delete()
        except:
            pass

        # Schedule the asynchronous 1-hour auto-delete countdown for all sent cards
        if sent_message_ids:
            asyncio.create_task(auto_delete_task(client, message.chat.id, sent_message_ids, delay=3600))
        return

    # DAFFA 2: Default standard operational configuration update route
    if len(message.command) < 2:
        return await message.reply("❌ <b>Usage Format Error:</b>\n\n⬡ <code>/forcesub -100xxxxxxxxxx</code> (Channel ID)\n⬡ <code>/forcesub username</code> (Without @ prefix)\n⬡ <code>/forcesub list</code>")
   
    raw_input = message.command[1]
    try:
        if raw_input.startswith("-") and raw_input[1:].isdigit(): target = int(raw_input)
        elif raw_input.isdigit(): target = int(raw_input)
        else: target = raw_input.replace("@", "")

        chat = await client.get_chat(target)
        member = await client.get_chat_member(chat.id, "me")
        if member.status != enums.ChatMemberStatus.ADMINISTRATOR: 
            return await message.reply("❌ <b>Bot Admin Nahi Hai!</b>\n\nPehle mujhe channel me Admin banao.")

        client.bot_db.add_forcesub(chat.id)
        status_msg = await message.reply("🔄 <b>Naya ForceSub mila! Sabhi users ko re-verify list mein daal raha hoon...</b>")
        
        try:
            members = list(client.bot_db.members.find({}, {"user_id": 1}))
            requests = list(client.bot_db.join_requests.find({}, {"user_id": 1}))
            for m in members + requests:
                client.bot_db.add_left_member(m["user_id"])
            client.bot_db.members.delete_many({})
            client.bot_db.join_requests.delete_many({})
            
            await status_msg.edit(
                f"✅ <b>ForceSub Added Successfully!</b>\n\n<b>Channel:</b> {chat.title}\n<b>ID:</b> <code>{chat.id}</code>\n\n"
                f"📢 <b>Sabhi users reset kar diye gaye hain.</b>"
            )
        except Exception as reset_err:
            logger.error(f"User Shift Error: {reset_err}")
            await status_msg.edit(f"✅ ForceSub added, but user reset failed: <code>{reset_err}</code>")
    except Exception as e: 
        await message.reply(f"❌ Error:\n<code>{str(e)}</code>")

@bot.on_message(ban_filter & filters.command("remove") & is_admin)
async def remove_forcesub_cmd(client, message: Message):
    if len(message.command) < 2: return await message.reply("❌ Usage:\n/remove -100123456789 (Channel ID) or /remove username")
    raw_input = message.command[1]
    try:
        if raw_input.startswith("-") and raw_input[1:].isdigit(): target = int(raw_input)
        elif raw_input.isdigit(): target = int(raw_input)
        else:
            target = raw_input.replace("@", "")
            chat = await client.get_chat(target)
            target = chat.id
        client.bot_db.remove_forcesub(target)
        await message.reply(f"✅ ForceSub channel removed successfully!\nID: `{target}`")
    except Exception as e: await message.reply(f"❌ Failed to remove ForceSub:\n`{str(e)}`")

@bot.on_message(ban_filter & filters.command("on") & is_admin)
async def protect_on(client, message: Message):
    client.bot_db.set_setting("protect_content", "1")
    await message.reply("🔒 **Forward Protection Enabled.**")

@bot.on_message(ban_filter & filters.command("off") & is_admin)
async def protect_off(client, message: Message):
    client.bot_db.set_setting("protect_content", "0")
    await message.reply("🔓 **Forward Protection Disabled.**")

@bot.on_message(ban_filter & filters.command("time") & is_admin)
async def set_time(client, message: Message):
    if len(message.command) < 2: return await message.reply("Usage: `/time 1 hour 30 min` or `/time off` ")
    input_str = message.text.split(None, 1)[1]
    if input_str.lower() == "off":
        client.bot_db.set_setting("delete_timer", "0")
        return await message.reply("⌛ Auto-delete disabled.")
    seconds = parse_duration(input_str)
    if not seconds: return await message.reply("Invalid format. Use: `1 hour`, `10 min`, etc.")
    client.bot_db.set_setting("delete_timer", str(seconds))
    client.bot_db.set_setting("delete_timer_readable", input_str)
    await message.reply(f"⌛ Auto-delete set to: **{input_str}**")

@bot.on_message(ban_filter & filters.command("back_up") & is_admin)
async def backup_db(client, message: Message):
    status_msg = await message.reply("🔄 **Processing Smart Backup...**")
    try:
        data = client.bot_db.export_data()
        
        total_clicks = 0
        batch_list = data.get('batches', {}).get('rows', [])
        for b in batch_list:
            try:
                clicks_list = json.loads(b.get("successful_clicks", "[]"))
                total_clicks += len(clicks_list)
            except: continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            file_path = f.name

        await message.reply_document(
            document=file_path,
            file_name=f"Sarena_Advanced_Backup_{datetime.now().strftime('%Y-%m-%d')}.json",
            caption=(
                "✅ **System Backup Successful**\n\n"
                f"📂 **Total Batches:** {len(batch_list)}\n"
                f"📈 **Total Successful Solves:** {total_clicks}\n"
                f"👤 **Total Users:** {len(data.get('members', {}).get('rows', []))}\n"
                "━━━━━━━━━━━━━━━━━━━━\n✨✨✨✨✨✨✨✨"
            )
        )
        await status_msg.delete()
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e:
        logger.error(f"Backup Command Error: {e}")
        await status_msg.edit(f"❌ **Backup Failed:**\n`{e}`")
        
@bot.on_message(ban_filter & filters.command("restore") & is_admin)
async def restore_db(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("❌ **Please reply to a valid backup.json file!**")
    status_msg = await message.reply("📥 **Restoring Database... Please wait.**")
    try:
        path = await message.reply_to_message.download()
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)
        client.bot_db.import_data(data)
        await status_msg.edit("✅ **Database Restored Successfully!**\n\n✨ Saara data (Batches, Users, Botlinks) update ho gaya hai.\n🔄 Bot ab naye settings ke saath taiyar hai.")
        if os.path.exists(path): os.remove(path)
    except Exception as e:
        logger.error(f"Restore error: {e}")
        await status_msg.edit(f"❌ **Restore Failed!**\n\n**Error:** `{str(e)}` \n\n💡 *Tip: Make sure you are using the latest backup file format.*")

@bot.on_message(ban_filter & filters.command("db") & is_admin)
async def reset_db_cmd(client, message: Message):
    status_msg = await message.reply("🔄 **Exporting and wiping Database...**")
    try:
        data = client.bot_db.export_data()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            file_path = f.name
        await message.reply_document(document=file_path, file_name=f"Wipe_Backup_{datetime.now().strftime('%Y-%m-%d')}.json", caption="✅ Database Exported before wipe.")
        
        # Wipe all collections
        for coll in client.bot_db.db.list_collection_names():
            client.bot_db.db[coll].delete_many({})
            
        await status_msg.edit("✅ **Database Exported and completely Wiped.**")
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e:
        await status_msg.edit(f"❌ **Wipe Failed:**\n`{e}`")


@bot.on_message(ban_filter & filters.command("clean") & filters.private)
async def clean_users_handler(client, message: Message):
    if not (message.from_user.id in OWNERS or client.bot_db.is_admin(message.from_user.id)):
        return await message.reply("❌ You are not authorized to use this command.")
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🍀Yᴇs 🫧 Cʟᴇᴀɴ", callback_data="confirm_clean"), InlineKeyboardButton("🍁 Cᴀɴᴄᴇʟ", callback_data="cancel_clean")]])
    await message.reply("**🍁 ʜᴇʏ sᴇɴᴘᴀɪ!😔**\n**ᴀᴘ sᴀʀᴇ ᴜsᴇʀs ᴄʟᴇᴀɴ ᴋᴀʀɴᴇ ᴡᴀʟᴇ ʜᴏ**\n\n**🍁 ᴘʟᴇᴀsᴇ ᴄᴏɴғɪʀᴍ**\n**❗ ʏᴇ ᴀᴄᴛɪᴏɴ ʀᴇᴠᴇʀsᴇ ɴᴀʜɪ ʜᴏ sᴀᴋᴛᴀ 💔**", reply_markup=buttons)

@bot.on_callback_query(filters.regex("confirm_clean"))
async def confirm_clean_handler(client, callback_query):
    if not (callback_query.from_user.id in OWNERS or client.bot_db.is_admin(callback_query.from_user.id)):
        return await callback_query.answer("❌ Not allowed.", show_alert=True)
    try:
        client.bot_db.clean_all_users()
        await callback_query.message.edit_text("🧹 **All users have been cleaned successfully.**\n\n👤 Total Users: 0")
    except Exception as e: await callback_query.message.edit_text(f"❌ Error while cleaning users:\n{e}")

@bot.on_callback_query(filters.regex("cancel_clean"))
async def cancel_clean_handler(client, callback_query):
    if not (callback_query.from_user.id in OWNERS or client.bot_db.is_admin(callback_query.from_user.id)):
        return await callback_query.answer("❌ Not allowed.", show_alert=True)
    await callback_query.message.edit_text("❌ Cleaning cancelled.")

async def is_on_cooldown(client, user_id):
    if user_id in OWNERS or client.bot_db.is_admin(user_id): return False
    now = time.time()
    if not hasattr(client, "user_cooldown"):
        client.user_cooldown = {}
    if user_id not in client.user_cooldown: client.user_cooldown[user_id] = []
    client.user_cooldown[user_id] = [ts for ts in client.user_cooldown[user_id] if now - ts < 60]
    if len(client.user_cooldown[user_id]) >= 5: return True
    client.user_cooldown[user_id].append(now)
    return False
 
# ==========================================
# --- PREMIUM MENU CALLBACKS ---
# ==========================================
PREMIUM_TEXT = """✨𝗘𝗫𝗖𝗟𝗨𝗦𝗜𝗩𝗘 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗠𝗘𝗠𝗕𝗘𝗥𝗦𝗛𝗜𝗣 ✨

 ᴜɴʟᴏᴄᴋ ᴀ ᴡᴏʀʟᴅ ᴏғ ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇғɪᴛs 

🔥 ᴘʀᴇᴍɪᴜᴍ ᴘᴇʀᴋs:
✔️ ᴅɪʀᴇᴄᴛ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋs – ɴᴏ ᴀᴅs, ɴᴏ ᴅɪsᴛʀᴀᴄᴛɪᴏɴ 💌
✔️ sᴘᴇᴄɪᴀʟ ᴀᴄᴄᴇss ᴛᴏ ᴇxᴄʟᴜsɪᴠᴇ ᴄᴏɴᴛᴇɴᴛ ✨
✔️ ғᴀsᴛᴇʀ sᴜᴘᴘᴏʀᴛ & ᴘʀɪᴏʀɪᴛʏ ʜᴇʟᴘ 

💭 ᴘʟᴜs, ʏᴏᴜ’ʟʟ ɢᴇᴛ ᴅɪʀᴇᴄᴛ ᴀᴄᴄᴇss ᴛᴏ ᴀʟʟ ᴄʜᴀɴɴᴇʟs 

💰 ᴘʀɪᴄɪɴɢ ᴘʟᴀɴs:
○ 7 ᴅᴀʏs — ɪɴʀ 40
○ 1 ᴍᴏɴᴛʜ — ɪɴʀ 100
○ 3 ᴍᴏɴᴛʜs — ɪɴʀ 200

📩 ʀᴇᴀᴅʏ ᴛᴏ ᴜᴘɢʀᴀᴅᴇ?
» ᴍᴇssᴀɢᴇ @Sgr_probot ғᴏʀ Upi / usdt / ton ǫʀ ᴄᴏᴅᴇ 💌

📸 ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ
ᴛᴏ @Sgr_probot ғᴏʀ ᴀᴜᴛᴏ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ✨

⚡ ʟɪᴍɪᴛᴇᴅ sᴇᴀᴛs ᴀᴠᴀɪʟᴀʙʟᴇ — ɢʀᴀʙ ʏᴏᴜʀs ɴᴏᴡ! 💗"""

# ==========================================
# --- PREMIUM MENU CALLBACKS (DYNAMIC OWNER) ---
# ==========================================

@bot.on_callback_query(filters.regex(r"^prem_show$"))
async def prem_show_cb(client, query: CallbackQuery):
    # Dynamic Owner ID nikalne ka logic
    if getattr(client, "is_clone", False):
        # Agar clone hai toh jisne clone kiya uski ID
        owner_id = getattr(client, "clone_owner", OWNERS[0])
    else:
        # Agar main bot hai toh aapki original ID
        owner_id = OWNERS[0]

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴏᴡɴᴇʀ", url=f"tg://openmessage?user_id={owner_id}")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ ᴛᴏ ʟɪɴᴋsʜᴏʀᴛɴᴇʀ", callback_data="prem_back")]
    ])
    
    if not hasattr(client, "temp_short_links"):
        client.temp_short_links = {}
        
    if query.message.id not in client.temp_short_links:
        client.temp_short_links[query.message.id] = {
            "caption": query.message.caption,
            "markup": query.message.reply_markup
        }
        
    await query.message.edit_caption(caption=PREMIUM_TEXT, reply_markup=btn)

@bot.on_callback_query(filters.regex(r"^prem_back$"))
async def prem_back_cb(client, query: CallbackQuery):
    if hasattr(client, "temp_short_links") and query.message.id in client.temp_short_links:
        data = client.temp_short_links[query.message.id]
        await query.message.edit_caption(caption=data["caption"], reply_markup=data["markup"])
    else:
        await query.answer("⚠️ Session expired, please Click Again On Bot Link)", show_alert=True)

# ==========================================
# --- Start Logic ---
# ==========================================

 
START_IMAGE = IMG_URL

#================= Start Buttons Update ============
def get_start_buttons(client, message):
    buttons = []
    is_clone = getattr(client, "is_clone", False)
    bot_id = client.me.id
    
    # Fetch customized button targets or use defaults seamlessly
    custom_btn_name = client.bot_db.get_custom_msg(bot_id, "BTN_NAME", DEFAULT_BTN_NAME)
    custom_btn_link = client.bot_db.get_custom_msg(bot_id, "BTN_LINK", CHANNEL_BUTTON_LINK)
    
    if is_clone:
        c_owner_id = getattr(client, "clone_owner", OWNERS[0])
        row1 = [
            InlineKeyboardButton("𝙳𝚎𝚟𝚎𝚕𝚘𝚙𝚎rer ❄️", url="tg://openmessage?user_id=6429574702"),
            InlineKeyboardButton("𝙾𝚠𝚗𝚎𝚛 ✨", url=f"tg://openmessage?user_id={c_owner_id}")
        ]
        buttons.append(row1)
    else:
        row1 = [
            InlineKeyboardButton("𝙳𝚎𝚟𝚎𝚕𝚘𝚙𝚎rer ❄️", url="tg://openmessage?user_id=6429574702"),
            InlineKeyboardButton("𝙾𝚠𝚗𝚎𝚛 ✨", url="tg://openmessage?user_id=8735285838")
        ]
        buttons.append(row1)
    
    # Custom Name & Link Applied dynamically below
    buttons.append([InlineKeyboardButton(custom_btn_name, url=custom_btn_link)])
    return InlineKeyboardMarkup(buttons)


@bot.on_message(ban_filter & filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    if await is_on_cooldown(client, user_id): return await message.reply("⚠️ **Please wait 1 minute before requesting another file.**")
    if len(message.command) < 2:
        custom_start_caption = client.bot_db.get_custom_msg(client.me.id, "START_CAPTION", DEFAULT_START_CAPTION)
        # Added disable_web_page_preview parameter securely inside reply_photo below
        return await message.reply_photo(
            photo=client.bot_db.get_bot_img(client.me.id, IMG_URL),
            caption=custom_start_caption.format(message=message),
            reply_markup=get_start_buttons(client, message)
        )

    param = message.command[1]

    if param.startswith("tok_"):
        batch_id, status = validate_token(client, param, user_id)
        if status == "invalid": return await message.reply("❌ Invalid or Unauthorized token.")
        if status == "expired":
            delete_token(client, param)
            return await message.reply("⏳ Link expired. Please get a new link.")

        is_joined, must_join_ids = await check_user_status(client, user_id)
        if not is_joined:
            buttons = []
            for chat_id in must_join_ids:
                link = await get_invite_link(client, chat_id)
                if link: buttons.append([InlineKeyboardButton(f"Join Channel", url=link)])
            buttons.append([InlineKeyboardButton("🌸 Try Again 🌸", url=f"https://t.me/{client.me.username}?start={param}")])
            # FIX: Exact string database fetch binding for saved custom forcesub layout
            custom_forcesub_text = client.bot_db.get_custom_msg(client.me.id, "FORCESUB", DEFAULT_FORCESUB_TEXT)
            try:
                caption_text = custom_forcesub_text.format(message=message)
            except Exception:
                caption_text = custom_forcesub_text

            return await message.reply_photo(
                photo=client.bot_db.get_bot_img(client.me.id, IMG_URL),
                caption=caption_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )



        if status == "bypass":
            delete_token(client, param)
            
            # --- PREMIUM USER KO DIRECT FILE DE DO (NO SHORTENER) ---
            if client.bot_db.is_premium(user_id):
                verify_button = InlineKeyboardMarkup([[InlineKeyboardButton("🍀 I am not a bot", callback_data=f"verify_{batch_id}")]])
                return await message.reply("**Human Verification Required**\n\nClick the button below to get your files.", reply_markup=verify_button)

            new_token = generate_token(client, user_id, batch_id)
            bot_link = f"https://t.me/{client.me.username}?start={new_token}"
            
            # Dynamic Active Config Collector Routing Logic
            config1 = client.bot_db.get_shortener_config(1)
            config2 = client.bot_db.get_shortener_config(2)
            active1 = client.bot_db.get_setting("SHORTENER_1_ACTIVE", "1") == "1"
            active2 = client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "1"
            
            # Alternate Routing State Matching for Tutorials & Assets mapping
            if active1 and active2:
                current_counter = int(client.bot_db.get_setting("ROUTING_COUNTER", "0"))
                selected_config = config1 if current_counter % 2 == 0 else config2
            elif active2 and config2.get("api"):
                selected_config = config2
            else:
                selected_config = config1

            short_link = await create_short_link(client, bot_link)
            tut_link = selected_config.get("tut") or client.bot_db.get_setting("TUTORIAL_LINK", TUTORIAL_LINK)
            
            # --- SIDE BY SIDE BUTTONS AUR PREMIUM BTN ---
            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("Dᴏᴡɴʟᴏᴀᴅ🪐", url=short_link), InlineKeyboardButton("📘 Tutorial", url=tut_link)],
                [InlineKeyboardButton("𝗣𝗥𝗘𝗠𝗜𝗨𝗠 ✨", callback_data="prem_show")]
            ])
            # BYPASS KEY LOOKUP FIXED HERE
            custom_bypass_text = client.bot_db.get_custom_msg(client.me.id, "BYPASS", DEFAULT_BYPASS_TEXT)
            msg = await message.reply_photo(
                photo=client.bot_db.get_bot_img(client.me.id, IMG_URL),
                caption=custom_bypass_text, 
                reply_markup=btn
            )

            asyncio.create_task(auto_delete_task(client, message.chat.id, [msg.id], TOKEN_EXPIRY_MINUTES * 60))
            return

        verify_button = InlineKeyboardMarkup([[InlineKeyboardButton("🍀 I am not a bot", callback_data=f"verify_{batch_id}")]])
        return await message.reply("**Human Verification Required**\n\nClick the button below to get your files.", reply_markup=verify_button)

    unique_id = param
    batch = client.bot_db.get_batch(unique_id)
    if not batch: return await message.reply("❌ Invalid or expired link.")

    try: msg_data, protect, link_mode, clicks = batch
    except: link_mode = 0

    is_joined, must_join_ids = await check_user_status(client, user_id)
    if not is_joined:
        buttons = []
        for chat_id in must_join_ids:
            link = await get_invite_link(client, chat_id)
            if link: buttons.append([InlineKeyboardButton(f"Join Channel", url=link)])
        buttons.append([InlineKeyboardButton("🌸 Try Again 🌸", url=f"https://t.me/{client.me.username}?start={param}")])
        # FIX: Exact string database fetch binding for saved custom forcesub layout (Normal batch view)
        custom_forcesub_text = client.bot_db.get_custom_msg(client.me.id, "FORCESUB", DEFAULT_FORCESUB_TEXT)
        try:
            caption_text = custom_forcesub_text.format(message=message)
        except Exception:
            caption_text = custom_forcesub_text

        return await message.reply_photo(
            photo=client.bot_db.get_bot_img(client.me.id, IMG_URL),
            caption=caption_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # --- NON-PREMIUM REGULAR SHORTENER LINK GENERATION ROUTING ---
    if link_mode == 1 and not client.bot_db.is_premium(user_id):
        token = generate_token(client, user_id, unique_id)
        bot_link = f"https://t.me/{client.me.username}?start={token}"
        
        # Dynamic Target Active Configuration Extractor Routine
        config1 = client.bot_db.get_shortener_config(1)
        config2 = client.bot_db.get_shortener_config(2)
        active1 = client.bot_db.get_setting("SHORTENER_1_ACTIVE", "1") == "1"
        active2 = client.bot_db.get_setting("SHORTENER_2_ACTIVE", "0") == "1"
        
        if active1 and active2:
            current_counter = int(client.bot_db.get_setting("ROUTING_COUNTER", "0"))
            selected_config = config1 if current_counter % 2 == 0 else config2
        elif active2 and config2.get("api"):
            selected_config = config2
        else:
            selected_config = config1

        short_link = await create_short_link(client, bot_link)
        if not short_link: return await message.reply("❌ Shortener API Error. Try again later.")
        tut_link = selected_config.get("tut") or client.bot_db.get_setting("TUTORIAL_LINK", TUTORIAL_LINK)
        
        # --- SIDE BY SIDE BUTTONS WITH UPDATED TUTORIAL TARGETS ---
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("Dᴏᴡɴʟᴏᴀᴅ🪐", url=short_link), InlineKeyboardButton("📘 Tutorial", url=tut_link)],
            [InlineKeyboardButton("𝗣𝗥𝗘𝗠𝗜𝗨𝗠 ✨", callback_data="prem_show")]
        ])
        # SHORTNER KEY LOOKUP FIXED HERE
        custom_shortner_text = client.bot_db.get_custom_msg(client.me.id, "SHORTNER", DEFAULT_SHORTNER_TEXT)
        msg = await message.reply_photo(
            photo=client.bot_db.get_bot_img(client.me.id, IMG_URL),
            caption=custom_shortner_text, 
            reply_markup=btn
        )

        asyncio.create_task(auto_delete_task(client, message.chat.id, [msg.id], TOKEN_EXPIRY_MINUTES * 60))
    else:
        verify_button = InlineKeyboardMarkup([[InlineKeyboardButton("🍀 I am not a bot", callback_data=f"verify_{unique_id}")]])
        await message.reply("**Solve Captcha!**\n\n**Human Verification**\n\n||🛡️ Anti bot protection||", reply_markup=verify_button)
    return
        
@bot.on_callback_query(filters.regex(r"^verify_"))
async def verify_user_handler(client, callback_query):
    user_id = callback_query.from_user.id
    unique_id = callback_query.data.split("_")[1]
    batch = client.bot_db.get_batch(unique_id)
    if not batch: return await callback_query.answer("Link expired!", show_alert=True)
    
    try: msg_ids_json, protect, _, _ = batch
    except: return await callback_query.answer("Database Error!", show_alert=True)
    msg_ids = json.loads(msg_ids_json)
    if len(msg_ids) > 60: return await callback_query.message.edit_text("Too many files in one batch. Contact admin.")
    await callback_query.message.delete()
    
    timer_seconds = int(client.bot_db.get_setting("delete_timer", "0"))
    sent_msgs = []      
    store_id = get_storage_id(client)
    
    if not store_id:
        return await callback_query.message.edit_text("⚠️ **Admin ne abhi tak Storage Channel configure nahi kiya hai.**")

    for m_id in msg_ids:      
        async with send_semaphore:      
            try:      
                copied = await client.copy_message(chat_id=callback_query.message.chat.id, from_chat_id=store_id, message_id=m_id, protect_content=bool(protect))      
                sent_msgs.append(copied.id)      
                await asyncio.sleep(0.2)      
            except FloodWait as e:      
                await asyncio.sleep(e.value)      
                copied = await client.copy_message(chat_id=callback_query.message.chat.id, from_chat_id=store_id, message_id=m_id, protect_content=bool(protect))      
                sent_msgs.append(copied.id)      
            except Exception as e: logger.error(f"Failed to copy message {m_id}: {e}")      

    try:
        current_clicks_json = batch[3] if len(batch) > 3 and batch[3] is not None else "[]"
        current_clicks = json.loads(current_clicks_json)
        if user_id not in current_clicks:
            current_clicks.append(user_id)
            client.bot_db.update_batch_clicks(unique_id, json.dumps(current_clicks))
    except Exception as e: logger.error(f"Click Tracking Error: {e}")
            
    if timer_seconds > 0:      
        readable = client.bot_db.get_setting("delete_timer_readable", f"{timer_seconds}s")      
        
        # KEY FETCH FIXED HERE TO MATCH AUTODEL MAPPING DEFINITIONS
        custom_warn_template = client.bot_db.get_custom_msg(client.me.id, "AUTODEL", DEFAULT_WARN_TEXT)
        warn_text = custom_warn_template.format(readable=readable)
        
        custom_btn_name = client.bot_db.get_custom_msg(client.me.id, "BTN_NAME", DEFAULT_BTN_NAME)
        custom_btn_link = client.bot_db.get_custom_msg(client.me.id, "BTN_LINK", CHANNEL_BUTTON_LINK)
        
        btn = InlineKeyboardMarkup([[InlineKeyboardButton(custom_btn_name, url=custom_btn_link)]])      
        # Added disable_web_page_preview parameter securely below
        warn_msg = await client.send_message(
            chat_id=callback_query.message.chat.id, 
            text=warn_text, 
            reply_markup=btn,
            disable_web_page_preview=True
        )      
        sent_msgs.append(warn_msg.id)      
        asyncio.create_task(auto_delete_task(client, callback_query.message.chat.id, sent_msgs, timer_seconds))  


    else:      
        success_text = "**✨ 𝗬𝗼𝘂𝗿 𝗙𝗶𝗹𝗲 𝗜𝘀 𝗛𝗲𝗿𝗲 ✨**\n**💖 𝗧𝗵𝗮𝗻𝒌𝘀 𝗙𝗼𝗿 𝗨𝘀𝗶𝗻𝗴 𝗘𝗹𝘆𝘀𝗶𝘂𝗺 𝗡𝗲𝘁𝘄𝗼𝗿𝗸**"      
        
        # FIX: Missing variables configuration context initialization added securely
        custom_btn_name = client.bot_db.get_custom_msg(client.me.id, "BTN_NAME", DEFAULT_BTN_NAME)
        custom_btn_link = client.bot_db.get_custom_msg(client.me.id, "BTN_LINK", CHANNEL_BUTTON_LINK)
        
        btn = InlineKeyboardMarkup([[InlineKeyboardButton(custom_btn_name, url=custom_btn_link)]])      
        await client.send_message(callback_query.message.chat.id, success_text, reply_markup=btn)



@bot.on_message(ban_filter & filters.command("show_links") & is_admin)
async def show_links_cmd(client, message: Message):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("📄 Normal Link List", callback_data="show_list_0_0")], [InlineKeyboardButton("🔗 Linkshortner List", callback_data="show_list_1_0")]])
    msg = await message.reply("📑 **Select What You Want to See (Link Type)**", reply_markup=buttons)
    asyncio.create_task(auto_delete_task(client, message.chat.id, [msg.id], 180))

@bot.on_callback_query(filters.regex(r"^show_list_"))
async def show_list_callback(client, query: CallbackQuery):
    data = query.data.split("_")
    mode = int(data[2]); page = int(data[3])
    limit = 10; offset = page * limit

    all_batches = list(client.bot_db.batches.find({"link_mode": mode}).skip(offset).limit(limit))
    total_links = client.bot_db.batches.count_documents({"link_mode": mode})

    if not all_batches and page == 0: return await query.answer("📭 Is category mein koi links nahi hain.", show_alert=True)

    header = "📄 **NORMAL LINKS**" if mode == 0 else "🔗 **LINKSHORTNER LINKS**"
    text = f"{header} (Page {page + 1})\n\n"
    for b in all_batches:
        uid = b["unique_id"]
        clicks_json = b.get("successful_clicks", "[]")
        clicks = len(json.loads(clicks_json))
        link = f"https://t.me/{client.me.username}?start={uid}"
        text += f"📍 `{link}`\n└─ ✅ Success: **[{clicks}]**\n\n"

    nav_buttons = []
    if page > 0: nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"show_list_{mode}_{page-1}"))
    if (page + 1) * limit < total_links: nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"show_list_{mode}_{page+1}"))
    control_buttons = [InlineKeyboardButton("🔙 Main Menu", callback_data="main_link_menu")]
    
    keyboard = []
    if nav_buttons: keyboard.append(nav_buttons)
    keyboard.append(control_buttons)
    try: await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    except MessageNotModified: pass

@bot.on_callback_query(filters.regex("main_link_menu"))
async def main_link_menu(client, query: CallbackQuery):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("📄 Normal Link List", callback_data="show_list_0_0")], [InlineKeyboardButton("🔗 Linkshortner List", callback_data="show_list_1_0")]])
    await query.message.edit_text("📑 **Select What You Want to See (Link Type)**", reply_markup=buttons)

@bot.on_message(ban_filter & filters.command("rm") & is_admin & filters.private)
async def remove_link_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.reply(f"🗑️**Usage Examples:**\n\n⬡ /rm abcdefgh \n⬡ /rm https://t.me/{client.me.username}?start=abcdefgh")
    input_data = message.command[1]
    if "start=" in input_data: unique_id = input_data.split("start=")[1]
    elif "/" in input_data: unique_id = input_data.split("/")[-1]
    else: unique_id = input_data

    batch = client.bot_db.get_batch(unique_id)
    if not batch: return await message.reply("❌ **Error:** Ye link ya ID database mein nahi mili.")
    try:
        client.bot_db.batches.delete_one({"unique_id": unique_id})
        client.bot_db.tokens.delete_many({"batch_id": unique_id})
        await message.reply(f"✅ **Successfully Removed!**\n\n🆔 **ID:** `{unique_id}`\n🗑️ Batch data aur usse jude saare tokens delete kar diye gaye hain.")
    except Exception as e:
        logger.error(f"Remove Link Error: {e}")
        await message.reply(f"❌ **Failed to remove:** `{e}`")

@bot.on_message(ban_filter & filters.command("broadcast") & is_admin)
async def broadcast_cmd_handler(client, message: Message):
    global broadcast_running
    if broadcast_running: return await message.reply("⚠️ **Ek broadcast pehle se chal raha hai.**\nUsey khatam hone dein ya cancel karein.")
    if not message.reply_to_message: return await message.reply("❌ **Kisi message ko reply karke /broadcast likhein.**")

    reply_msg = message.reply_to_message
    await message.reply("🚀 **Broadcast Start Ho Raha Hai...**")
    asyncio.create_task(start_broadcast_engine(client, message, reply_msg))

@bot.on_callback_query(filters.regex(r"^bc_"))
async def broadcast_callback_handler(client, query: CallbackQuery):
    global broadcast_paused, broadcast_cancelled
    action = query.data.split("_")[1]
    if action == "pause":
        broadcast_paused = True
        await query.answer("Paused ⏸️")
        await query.message.edit_reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Resume", callback_data="bc_resume"), InlineKeyboardButton("🚫 Cancel", callback_data="bc_cancel")]]))
    elif action == "resume":
        broadcast_paused = False
        await query.answer("Resumed ▶️")
        await query.message.edit_reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("⏸️ Pause", callback_data="bc_pause"), InlineKeyboardButton("🚫 Cancel", callback_data="bc_cancel")]]))
    elif action == "cancel":
        broadcast_cancelled = True
        await query.answer("Cancelling... 🚫")

async def start_broadcast_engine(client, message: Message, reply_msg: Message):
    global broadcast_running, broadcast_paused, broadcast_cancelled
    
    users1 = [doc["user_id"] for doc in client.bot_db.members.find({}, {"user_id": 1})]
    users2 = [doc["user_id"] for doc in client.bot_db.join_requests.find({}, {"user_id": 1})]
    users3 = [doc["user_id"] for doc in client.bot_db.left_members.find({}, {"user_id": 1})]
    all_users = list(set(users1 + users2 + users3))
    
    total_users = len(all_users)
    done = failed = success = 0
    broadcast_running = True; broadcast_paused = broadcast_cancelled = False
    status_text = "📊 **ʙʀᴏᴀᴅᴄᴀsᴛ {status}** 🍀\n\n**Tᴏᴛᴀʟ Usᴇʀs :** {total}\n👤 **ᴜsᴇʀs sᴇɴᴛ:** {success}\n**×̷̷͜×̷ ғᴀɪʟᴇᴅ ᴜsᴇʀs:** {failed}\n\n**ʟɪᴠᴇ ᴘʀᴏɢʀᴇss:** {percent}%"
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("⏸️ Pause", callback_data="bc_pause"), InlineKeyboardButton("🚫 Cancel", callback_data="bc_cancel")]])
    progress_msg = await reply_msg.reply(status_text.format(status="Running", total=total_users, success=0, failed=0, percent=0), reply_markup=buttons)

    last_update_time = time.time()
    for user_id in all_users:
        if broadcast_cancelled: break
        while broadcast_paused:
            await asyncio.sleep(1)
            if broadcast_cancelled: break
        try:
            async with send_semaphore:
                await reply_msg.copy(chat_id=user_id)
                success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            await reply_msg.copy(chat_id=user_id)
            success += 1
        except Exception:
            failed += 1
            client.bot_db.members.delete_one({"user_id": user_id})
            client.bot_db.join_requests.delete_one({"user_id": user_id})
            client.bot_db.left_members.delete_one({"user_id": user_id})

        done += 1
        if (time.time() - last_update_time) > 5 or done == total_users:
            percent = round((done / total_users) * 100, 2) if total_users else 0
            try:
                await progress_msg.edit_text(status_text.format(status="Running" if not broadcast_paused else "Paused", total=total_users, success=success, failed=failed, percent=percent), reply_markup=buttons)
                last_update_time = time.time()
            except: pass

    broadcast_running = False
    final_status = "✅ Completed" if not broadcast_cancelled else "❌ Cancelled"
    await progress_msg.edit_text(f"📊 **ʙʀᴏᴀᴅᴄᴀsᴛ {final_status}**\n\nFinal Success: {success}\nFinal Failed: {failed} (Removed from DB)")

@bot.on_message(ban_filter & filters.private & ~filters.command(["file", "end", "start", "help","stats","broadcast","link","rm","Show_links","linkshortner","st","db","clone","clone_list","add_admin","remove_admin","admin_list","ban","unban"]) & is_admin)
async def collection_listener(client, message: Message):
    user_id = message.from_user.id
    if user_id in client.collecting_users:
        store_id = get_storage_id(client)
        if not store_id:
            return await message.reply("⚠️ **Storage channel set nahi hai!** Pehle `/st <channel_id>` command se storage set karein.", quote=True)
            
        try:
            copied = await message.copy(store_id)
            client.collecting_users[user_id]["messages"].append(copied.id)
            await message.reply("File Saved ✅", quote=True) 
        except Exception as e:
            await message.reply(f"❌ **File save nahi hui!**\n\n**Error:** `{e}`\n*Check karein ki kya aapne bot ko apne Storage Channel me Admin banaya hai.*", quote=True)

@bot.on_chat_member_updated()
async def member_update_handler(client, update):
    if update.new_chat_member and update.new_chat_member.status == enums.ChatMemberStatus.LEFT:
        user_id = update.new_chat_member.user.id
        client.bot_db.add_left_member(user_id)
        client.bot_db.remove_join_request(user_id)

    if not update.new_chat_member:
        user_id = update.old_chat_member.user.id
        client.bot_db.update_member(user_id, "left")
        client.bot_db.add_left_member(user_id)
        client.bot_db.remove_join_request(user_id)
    else:
        user_id = update.new_chat_member.user.id
        client.bot_db.update_member(user_id, "member")
        client.bot_db.remove_join_request(user_id)
        client.bot_db.remove_left_member(user_id)

@bot.on_chat_join_request()
async def join_request_handler(client, request):
    client.bot_db.add_join_request(request.from_user.id)

# --- EXECUTION ---
if __name__ == "__main__":
    try:
        main_bot_id = int(BOT_TOKEN.split(":")[0])
        main_db = get_db(main_bot_id)
        
        loop = asyncio.get_event_loop()
        clones = main_db.get_all_clones()
        
        async def start_clones():
            for c in clones:
                try:
                    c_token = c["token"]
                    new_clone = FileStoreBot(
                        name=f"clone_{c_token.split(':')[0]}", 
                        bot_token=c_token, 
                        api_id=API_ID, 
                        api_hash=API_HASH, 
                        plugins=None,
                        in_memory=True
                    )
                    new_clone.is_clone = True
                    new_clone.clone_owner = c["owner_id"]
                    await new_clone.start()
                    
                    for group, handlers in bot.dispatcher.groups.items():
                        for handler in handlers:
                            new_clone.add_handler(handler, group)
                            
                    active_clones.append(new_clone)
                except Exception as e: 
                    logger.error(f"Failed to load clone {c.get('bot_id', 'Unknown')}: {e}")
                
        loop.run_until_complete(start_clones())
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.error(f"Fatal Error: {e}")