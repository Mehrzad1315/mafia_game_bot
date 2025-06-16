import logging
import random
import uuid
import os
import sys

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.error import Conflict, NetworkError

# مراحل مکالمه
SELECT_SCENARIO, SELECT_PLAYER_COUNT = range(2)

# کاربران فعال
registered_users = set()

games = {}

user_states = {}

# سناریوها و نقش‌ها
SCENARIOS = {
    "Takavar": {
        10: ["ريیس مافیا", "گروگانگیر", "ناتو", "کاراگاه", "دکتر",
             "نگهبان", "تکاور", "تفنگدار", "شهروند ساده", "شهروند ساده"],
        11: ["ريیس مافیا", "گروگانگیر", "ناتو", "کاراگاه", "دکتر",
             "نگهبان", "تکاور", "تفنگدار", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        12: ["ريیس مافیا", "گروگانگیر", "ناتو", "مافیا ساده", "کاراگاه", "دکتر",
             "نگهبان", "تکاور", "تفنگدار", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        13: ["ريیس مافیا", "گروگانگیر", "ناتو", "مافیا ساده", "کاراگاه", "دکتر",
             "نگهبان", "تکاور", "تفنگدار", "شهروند ساده", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        14: ["ريیس مافیا", "گروگانگیر", "ناتو", "مافیا ساده", "کاراگاه", "دکتر",
             "نگهبان", "تکاور", "تفنگدار", "شهروند ساده", "شهروند ساده", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        15: ["ريیس مافیا", "گروگانگیر", "ناتو", "مافیا ساده", "مافیا ساده", "کاراگاه", "دکتر",
             "نگهبان", "تکاور", "تفنگدار", "شهروند ساده", "شهروند ساده", "شهروند ساده", "شهروند ساده", "شهروند ساده"]
    },
    "Bazpors": {
        10: ["ريیس مافیا", "ناتو", "شیاد", "کاراگاه", "دکتر",
             "رویین تن", "محقق(هانتر)", "بازپرس", "شهروند ساده", "شهروند ساده"],
        11: ["ريیس مافیا", "ناتو", "شیاد", "کاراگاه", "دکتر",
             "رویین تن", "محقق(هانتر)", "بازپرس", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        12: ["ريیس مافیا", "ناتو", "شیاد", "مافیا ساده", "کاراگاه", "دکتر",
             "رویین تن", "محقق(هانتر)", "بازپرس", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        13: ["ريیس مافیا", "ناتو", "شیاد", "مافیا ساده", "کاراگاه", "دکتر",
             "رویین تن", "محقق(هانتر)", "بازپرس", "شهروند ساده", "تک تیرانداز", "شهروند ساده", "شهروند ساده"],
        14: ["ريیس مافیا", "ناتو", "شیاد", "مافیا ساده", "کاراگاه", "دکتر",
             "رویین تن", "محقق(هانتر)", "بازپرس", "شهروند ساده", "تک تیرانداز", "شهروند ساده", "شهروند ساده", "شهروند ساده"],                         
        15: ["ريیس مافیا", "ناتو", "شیاد", "مافیا ساده", "مافیا ساده", "کاراگاه", "دکتر",
             "رویین تن", "محقق(هانتر)", "بازپرس", "شهروند ساده", "تک تیرانداز", "شهروند ساده", "شهروند ساده", "شهروند ساده"]
    },
    "Namayandeh": {
        10: ["دن مافیا", "یاغی", "هکر", "دکتر", "راهنما",
             "مین گذار", "وکیل", "محافظ", "شهروند ساده", "شهروند ساده"],
        11: ["دن مافیا", "یاغی", "هکر", "دکتر", "راهنما",
             "مین گذار", "وکیل", "محافظ", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        12: ["دن مافیا", "یاغی", "هکر", "ناتو", "دکتر", "راهنما",
             "مین گذار", "وکیل", "محافظ", "سرباز", "شهروند ساده", "شهروند ساده"],
        13: ["دن مافیا", "یاغی", "هکر", "ناتو", "دکتر", "راهنما",
             "مین گذار", "وکیل", "محافظ", "سرباز", "شهروند ساده", "شهروند ساده", "شهروند ساده"],
        14: ["دن مافیا", "یاغی", "هکر", "ناتو", "دکتر", "راهنما",
             "مین گذار", "وکیل", "محافظ", "سرباز", "شهروند ساده", "شهروند ساده", "شهروند ساده", "شهروند ساده"],                         
        15: ["دن مافیا", "یاغی", "هکر", "ناتو", "مافیا ساده", "دکتر", "راهنما",
             "مین گذار", "وکیل", "محافظ", "سرباز", "شهروند ساده", "شهروند ساده", "شهروند ساده", "شهروند ساده"]
    }
}

games = {}
logging.basicConfig(level=logging.INFO)


def get_game_buttons(game_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Join Game", callback_data=f"join_{game_id}")],
        [InlineKeyboardButton("📋 View Players", callback_data=f"view_{game_id}")],
        [InlineKeyboardButton("➕ Add Fake Players", callback_data=f"add_fake_players|{game_id}")],
        [InlineKeyboardButton("🚀 Start Game", callback_data=f"startbtn_{game_id}")],
        [InlineKeyboardButton("🎯 End Game", callback_data=f"endgame_{game_id}")],
        [InlineKeyboardButton("🔄 Restart Game", callback_data=f"restartbtn_{game_id}")]
    ])

def get_game_info_text(game_id):
    """Generate game information text with creator name"""
    game = games.get(game_id)
    if not game:
        return "⛔️ بازی یافت نشد."
    
    creator_name = game.get('creator_name', 'نامشخص')
    scenario = game.get('scenario', 'انتخاب نشده')
    player_count = game.get('player_count', 0)
    current_players = len(game.get('players', []))
    
    text = f"🎮 بازی توسط: **{creator_name}**\n"
    text += f"🎭 سناریو: {scenario}\n"
    text += f"👥 بازیکنان: {current_players}/{player_count}\n"
    text += "─" * 25 + "\n"
    
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    # اگر پارامتر داره و join_ هست، یعنی لینک جوین رو زده
    if args and args[0].startswith("join_"):
        game_id = args[0][5:]

        if game_id not in games:
            await update.message.reply_text("⛔️ بازی مورد نظر پیدا نشد.")
            return

        # ذخیره game_id برای استفاده در join_button
        context.user_data["game_id_to_join"] = game_id

        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("✅ فعال‌سازی حساب", callback_data="activate_account")
        )
        await update.message.reply_text(
            "برای ورود به بازی، ابتدا باید حساب خود را فعال کنید. لطفاً روی دکمه زیر بزنید:",
            reply_markup=keyboard
        )
        return


async def activate_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    registered_users.add(user_id)
    await query.answer()

    await query.edit_message_text("✅ حساب شما با موفقیت فعال شد! حالا می‌تونید در بازی‌ها شرکت کنید.")

    # اگر کاربر با لینک join وارد شده بود، بعد از فعال‌سازی، خودش براش join button بفرسته
    game_id = context.user_data.get("game_id_to_join")
    if game_id:
        keyboard = get_game_buttons(game_id)
        await context.bot.send_message(
            chat_id=user_id,
            text="برای ورود به بازی، روی دکمه زیر بزن:",
            reply_markup=keyboard
    )

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    # FIXED: Store the original chat ID where the game was started
    original_chat_id = update.effective_chat.id

    # بررسی اینکه آیا کاربر قبلاً بازی ساخته یا نه
    existing_game_id = None
    for gid, game in games.items():
        if game['creator_id'] == user_id:
            existing_game_id = gid
            break

    if existing_game_id:
        # ذخیره game_id برای استفاده بعدی
        context.user_data["existing_game_id"] = existing_game_id
        # FIXED: Update the original chat ID for existing game
        games[existing_game_id]['original_chat_id'] = original_chat_id

        bot_username = (await context.bot.get_me()).username
        await update.message.reply_text(
            f"🟢 بازی‌ای که ساختی قبلاً فعال شده. بازیکن‌ها می‌تونن از لینک استفاده کنن و جوین بشن.\n"
            f"📎 لینک: https://t.me/{bot_username}?start=join_{existing_game_id}"
        )

        # ذخیره اطلاعات پیام سناریو برای حذف بعدی
        scenario_message = await update.message.reply_text(
            "🎭 لطفاً یک سناریو انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(
                [[s] for s in SCENARIOS.keys()],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        
        # ذخیره اطلاعات پیام برای حذف بعدی
        games[existing_game_id]['scenario_message_id'] = scenario_message.message_id
        games[existing_game_id]['scenario_message_chat_id'] = scenario_message.chat_id

        return SELECT_SCENARIO

    # ساخت بازی جدید
    game_id = str(uuid.uuid4())

    games[game_id] = {
        'creator_id': user_id,
        'creator_name': user_name,
        'players': [],
        'scenario': None,
        'player_count': None,
        # FIXED: Store the original chat ID where the game was started
        'original_chat_id': original_chat_id
    }

    context.user_data["existing_game_id"] = game_id

    # ذخیره اطلاعات پیام سناریو برای حذف بعدی
    scenario_message = await update.message.reply_text(
        "🎭 لطفاً یک سناریو انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [[s] for s in SCENARIOS.keys()],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    
    # ذخیره اطلاعات پیام برای حذف بعدی
    games[game_id]['scenario_message_id'] = scenario_message.message_id
    games[game_id]['scenario_message_chat_id'] = scenario_message.chat_id

    return SELECT_SCENARIO



async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    game_id = query.data.split("_", 1)[1]
    game = games.get(game_id)

    if not game:
        await query.edit_message_text("⛔️ بازی یافت نشد.")
        return

    if user.id != game['creator_id']:
        await context.bot.send_message(chat_id=user.id, text="⛔️ فقط سازنده بازی می‌تواند بازی را پایان دهد.")
        return

    players = game['players']
    roles = game['roles']

    if len(players) != len(roles):
        await query.edit_message_text("بازی با موفقیت پایان یافت")
        del games[game_id]
        return ConversationHandler.END

    creator_name = game.get('creator_name', 'نامشخص')
    text = f"🎯 بازی '{creator_name}' پایان یافت!\n\n🔍 لیست نقش‌ها:\n\n"
    for player, role in zip(players, roles):
        text += f"👤 {player['name']}: 🎭 {role}\n"

    # FIXED: Get the original chat ID where the game was started
    original_chat_id = game.get('original_chat_id')
    
    # حذف بازی از حافظه
    del games[game_id]

    # FIXED: Send to the original group chat where the game was started
    try:
        if original_chat_id:
            await context.bot.send_message(chat_id=original_chat_id, text=text)
            await query.edit_message_text("✅ بازی با موفقیت پایان یافت و نقش‌ها ارسال شد.")
        else:
            # Fallback to current chat if original_chat_id is not available
            await context.bot.send_message(chat_id=query.message.chat_id, text=text)
            await query.edit_message_text("✅ بازی با موفقیت پایان یافت و نقش‌ها ارسال شد.")
    except Exception as e:
        await query.edit_message_text("❌ خطا در ارسال پیام پایان بازی.")
        print("🔴 Error sending end game message:", e)

async def restart_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    game_id = query.data.split("_", 1)[1]
    game = games.get(game_id)

    if not game:
        await query.edit_message_text("⛔️ بازی پیدا نشد.")
        return ConversationHandler.END

    if user.id != game['creator_id']:
        await context.bot.send_message(chat_id=user.id, text="⛔️ فقط سازنده می‌تونه بازی رو ری‌استارت کنه.")
        return ConversationHandler.END

    # FIXED: Store the original chat ID before deleting the game
    original_chat_id = game.get('original_chat_id')
    
    # حذف بازی
    del games[game_id]
    context.user_data.clear()

    # ذخیره اطلاعات پیام سناریو برای حذف بعدی
    scenario_message = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🎭 لطفاً یک سناریو انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [[s] for s in SCENARIOS.keys()],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

    # ساخت بازی جدید
    new_game_id = str(uuid.uuid4())
    games[new_game_id] = {
        'creator_id': user.id,
        'players': [],
        'scenario': None,
        'player_count': None,
        'scenario_message_id': scenario_message.message_id,
        'scenario_message_chat_id': scenario_message.chat_id,
        # FIXED: Preserve the original chat ID
        'original_chat_id': original_chat_id
    }
    
    context.user_data["existing_game_id"] = new_game_id

    return SELECT_SCENARIO

async def select_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = None
    scenario = None
    game_id = context.user_data.get("existing_game_id")

    # اگر آپدیت از نوع CallbackQuery باشه (یعنی کاربر دکمه رو زده)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        scenario = query.data
    # اگر آپدیت از نوع پیام متنی باشه (یعنی کاربر سناریو رو تایپ کرده)
    elif update.message:
        user_id = update.message.from_user.id
        scenario = update.message.text

    if not game_id or game_id not in games:
        await update.effective_chat.send_message("⛔️ مشکلی در بازی وجود دارد. لطفاً دوباره بازی را شروع کنید.")
        return ConversationHandler.END

    # بررسی اینکه آیا کاربر سازنده بازی است یا نه
    if games[game_id]['creator_id'] != user_id:
        # اگر کاربر سازنده نیست، هیچ کاری انجام نمی‌دهیم
        if update.message:
            await update.message.reply_text("⛔️ فقط سازنده بازی می‌تواند سناریو را انتخاب کند.")
        return SELECT_SCENARIO

    if scenario not in SCENARIOS:
        await update.effective_chat.send_message("⛔️ سناریوی نامعتبر. لطفاً یکی از گزینه‌های موجود را انتخاب کنید.")
        return SELECT_SCENARIO

    # ذخیره سناریو
    games[game_id]['scenario'] = scenario
    context.user_data['scenario'] = scenario

    # پاک کردن پیام لیست سناریوها از گروه
    scenario_msg_id = games[game_id].get('scenario_message_id')
    scenario_chat_id = games[game_id].get('scenario_message_chat_id')

    if scenario_msg_id and scenario_chat_id:
        try:
            await context.bot.delete_message(
                chat_id=scenario_chat_id,
                message_id=scenario_msg_id
            )
        except Exception as e:
            print(f"خطا در حذف پیام سناریو از گروه: {e}")

    # ارسال پیام تایید انتخاب سناریو
    await update.effective_chat.send_message(
        f"✅ سناریو انتخاب شد: {scenario}\n\n🔢 حالا تعداد بازیکنان را وارد کنید (بین 10 تا 15):",
        reply_markup=ReplyKeyboardRemove()
    )

    return SELECT_PLAYER_COUNT


async def select_player_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game_id = context.user_data.get('existing_game_id')

    if not game_id:
        await update.message.reply_text("⛔️ بازی یافت نشد. لطفاً بازی را دوباره شروع کنید.")
        return ConversationHandler.END

    if game_id not in games:
        await update.message.reply_text("⛔️ بازی یافت نشد. لطفاً بازی را دوباره شروع کنید.")
        return ConversationHandler.END

    if games[game_id]['creator_id'] != user_id:
        await update.message.reply_text("⛔️ فقط سازنده بازی می‌تواند تعداد بازیکنان را تعیین کند.")
        return SELECT_PLAYER_COUNT

    scenario = games[game_id].get('scenario')
    if scenario is None:
        await update.message.reply_text("⛔️ سناریوی بازی یافت نشد. لطفاً بازی را دوباره شروع کنید.")
        return ConversationHandler.END

    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("⛔️ لطفاً فقط عدد وارد کنید.")
        return SELECT_PLAYER_COUNT

    count = int(text)

    if count < 10 or count > 15:
        await update.message.reply_text("⛔️ تعداد بازیکنان باید بین ۱۰ تا ۱۵ باشد. لطفاً عدد معتبر وارد کنید.")
        return SELECT_PLAYER_COUNT

    roles = SCENARIOS.get(scenario, {}).get(count)
    if not roles:
        await update.message.reply_text("⛔️ نقش‌هایی برای تعداد بازیکن انتخاب شده یافت نشد.")
        return SELECT_PLAYER_COUNT

    games[game_id]['player_count'] = count
    games[game_id]['roles'] = roles

    bot_username = (await context.bot.get_me()).username
    bot_link = f"https://t.me/{bot_username}?start=join_{game_id}"

    keyboard = get_game_buttons(game_id)
    game_info = get_game_info_text(game_id)

    await update.message.reply_text(
        f"{game_info}"
        f"🎮 بازی '{scenario}' با {count} بازیکن تنظیم شد.\n"
        f"برای شرکت، ابتدا وارد ربات شوید و دکمه فعال‌سازی را بزنید:\n"
        f"{bot_link}\n\n"
        f"سپس روی دکمه Join Game کلیک کنید.",
        reply_markup=keyboard
    )

    return ConversationHandler.END



async def join_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    game_id = query.data.split("_", 1)[1]
    game = games.get(game_id)

    if not game:
        await query.answer("⛔️ بازی یافت نشد.", show_alert=True)
        return

    if user.id not in registered_users:
        await context.bot.send_message(
            chat_id=user.id,
            text="❗️ لطفاً ابتدا وارد ربات شوید و دکمه '✅ فعال‌سازی حساب' را بزنید."
        )
        return

    if any(p['id'] == user.id for p in game['players']):
        await context.bot.send_message(chat_id=user.id, text="⛔️ شما قبلاً ثبت‌نام کرده‌اید.")
        return

    if len(game['players']) >= game['player_count']:
        await context.bot.send_message(chat_id=user.id, text="⛔️ ظرفیت بازی تکمیل شده.")
        return

    game['players'].append({'id': user.id, 'name': user.first_name})
    await context.bot.send_message(chat_id=user.id, text="✅ شما به بازی پیوستید. بازی بعد از جوین شدن همه بازیکن ها توسط سازنده شروع میشود و نقش خود را خواهد دید. میتوانید با کلیک روی View Players لیست بازیکن های اضافه شده را ببینید")
    await query.answer("✅ شما به بازی اضافه شدید.")


async def add_fake_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    parts = query.data.split("|", 1)
    if len(parts) < 2:
        await query.edit_message_text("خطا در داده ورودی.")
        return
    game_id = parts[1]

    game = games.get(game_id)
    if not game:
        await query.edit_message_text("بازی پیدا نشد.")
        return

    if game['creator_id'] != user_id:
        await query.edit_message_text("فقط سازنده بازی می‌تواند فیک پلیر اضافه کند.")
        return

    max_players = game['player_count']
    current_players = len(game['players'])
    num_needed = max_players - current_players

    if num_needed <= 0:
        await query.edit_message_text("ظرفیت بازی کامل است. نیازی به فیک پلیر نیست.")
        return

    for i in range(num_needed):
        fake_id = str(uuid.uuid4())
        fake_name = f"🤖 فیک پلیر {current_players + i + 1}"
        game['players'].append({'id': fake_id, 'name': fake_name})

    keyboard = get_game_buttons(game_id)

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=f"{num_needed} فیک پلیر اضافه شد. حالا می‌تونید بازی رو شروع کنید.",
        reply_markup=keyboard
    )

async def start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    game_id = query.data.split("_", 1)[1]
    game = games.get(game_id)

    if not game:
        await query.edit_message_text("⛔️ بازی یافت نشد.")
        return

    if user.id != game['creator_id']:
        await context.bot.send_message(chat_id=user.id, text="⛔️ فقط سازنده می‌تواند بازی را شروع کند.")
        return

    if len(game['players']) != game['player_count']:
        await context.bot.send_message(chat_id=user.id, text="⛔️ بازیکنان کامل نیستند.")
        return

    random.shuffle(game['roles'])
    for i, player in enumerate(game['players']):
        role = game['roles'][i]
        try:
            await context.bot.send_message(chat_id=player['id'], text=f"🎭 نقش شما: {role}")
        except Exception:
            await update.effective_message.reply_text(f"❗️ نتوانستم پیام برای {player['name']} بفرستم.")

    await query.edit_message_text("✅ نقش‌ها ارسال شد. بازی شروع شد!")


async def view_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        print(f"❌ Failed to answer callback query: {e}")

    user = query.from_user
    game_id = query.data.split("_", 1)[1]
    game = games.get(game_id)

    if not game:
        await query.edit_message_text("⛔️ بازی پیدا نشد.")
        return

    players = game['players']
    player_count = len(players)
    max_players = game['player_count']

    if player_count == 0:
        text = "❗️ هنوز بازیکنی وارد بازی نشده است."
    else:
        text = f"👥 بازیکنان فعلی ({player_count}/{max_players}):\n\n"
        for idx, player in enumerate(players, 1):
            text += f"{idx}. {player['name']}\n"

        if player_count == max_players:
            text += "\n✅ همه بازیکنان وارد شدند. می‌توانید بازی را شروع کنید."

    await context.bot.send_message(chat_id=user.id, text=text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔️ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Error handling function
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors and conflicts"""
    if isinstance(context.error, Conflict):
        logging.error("Conflict error: Another bot instance is running")
        # Try to continue running instead of crashing
        return
    elif isinstance(context.error, NetworkError):
        logging.error(f"Network error: {context.error}")
        # Try to continue running
        return
    else:
        logging.error(f"Update {update} caused error {context.error}")

def main():
    """Main function with proper error handling"""
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        print("❌ BOT_TOKEN environment variable not set!")
        sys.exit(1)
    
    # Create application with error handling
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(activate_account, pattern="^activate_account$"))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("startgame", startgame),
            CallbackQueryHandler(restart_button, pattern="^restartbtn_")
        ],
        states={
            SELECT_SCENARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_scenario)],
            SELECT_PLAYER_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_player_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(join_button, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(start_button, pattern="^startbtn_"))
    app.add_handler(CallbackQueryHandler(view_players, pattern="^view_"))
    app.add_handler(CallbackQueryHandler(add_fake_players, pattern=r"^add_fake_players\|"))
    app.add_handler(CallbackQueryHandler(end_game, pattern="^endgame_"))
    app.add_handler(CallbackQueryHandler(restart_button, pattern="^restartbtn_"))

    # Run with error handling
    try:
        print("🤖 Starting bot...")
        app.run_polling(
            poll_interval=1.0,  # Reduced polling interval
            timeout=10,         # Reduced timeout
            drop_pending_updates=True  # Drop pending updates on startup
        )
    except Conflict as e:
        print(f"❌ Conflict error: {e}")
        print("💡 Another instance of the bot might be running. Please stop other instances.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
