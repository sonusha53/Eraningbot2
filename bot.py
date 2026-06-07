import os
import telebot
from threading import Thread
from flask import Flask

# ==================== RENDER TIMEOUT FIX (FAKE SERVER) ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Live!"

def run():
    # Render jo port dega uspar server chalega
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
# =========================================================================

BOT_TOKEN = "8984080434:AAHn0dvGU4FOumJhfRFXzk2-FWHtELq4eQg"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = "8063553847"        
BOT_USERNAME = "ASKTORNAMENT_BOT"  
SUPPORT_USERNAME = "gainoffiicialnick"  

MAIN_CHANNEL = "eraningwithask9" 
YOUTUBE_LINK = "https://youtube.com/@AapkaChannel" # 👈 Yahan apna YouTube link daal dena bas

REFER_BONUS = 5
TELEGRAM_TASK_BONUS = 2   
YOUTUBE_TASK_BONUS = 3    
MIN_WITHDRAW = 20

users_db = {}
withdraw_requests = []
task_requests = [] 

def check_join(user_id):
    try:
        member = bot.get_chat_member(f"@{MAIN_CHANNEL}", int(user_id))
        if member.status in ['left', 'kicked']:
            return False
        return True
    except:
        return True

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    
    if user_id not in users_db:
        users_db[user_id] = {'balance': 0, 'referred_by': None, 'ref_count': 0, 'joined': False, 'tasks': {'tg': False, 'yt': False}}
        text_split = message.text.split()
        if len(text_split) > 1:
            referrer_id = text_split[1]
            if referrer_id != user_id and referrer_id in users_db:
                users_db[user_id]['referred_by'] = referrer_id

    if not check_join(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="📢 Join Channel", url=f"https://t.me/{MAIN_CHANNEL}"))
        markup.add(telebot.types.InlineKeyboardButton(text="✅ Joined / Verify", callback_data="verify_join"))
        bot.send_message(message.chat.id, f"❌ Access Denied!\n\nBot use karne ke liye aapko hamare official channel @{MAIN_CHANNEL} ko join karna hoga. Join karke niche diye gaye Verify button par click karein:", reply_markup=markup)
        return

    main_menu(message.chat.id, username)

def main_menu(chat_id, username):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 My Profile", "🔗 Refer & Earn")
    markup.add("💰 Earning Tasks 🚀", "💰 Withdraw Money")
    markup.add("📞 Support")
    bot.send_message(chat_id, f"👋 Welcome {username} to Earning Bot!\n\nYahan aap tasks poore karke aur dosto ko refer karke real cash kama sakte hain.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    user_id = str(call.from_user.id)
    if check_join(user_id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        if users_db.get(user_id) and users_db[user_id]['referred_by'] and not users_db[user_id]['joined']:
            ref_id = users_db[user_id]['referred_by']
            if ref_id in users_db:
                users_db[ref_id]['balance'] += REFER_BONUS
                users_db[ref_id]['ref_count'] += 1
                try: bot.send_message(ref_id, f"🎉 Naya Referral! Aapke link se user ne channel join kiya. Aapko ₹{REFER_BONUS} mile!")
                except: pass
                    
        if user_id in users_db:
            users_db[user_id]['joined'] = True
            
        bot.answer_callback_query(call.id, "✅ Verification Successful!", show_alert=True)
        main_menu(call.message.chat.id, call.from_user.username or "User")
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.from_user.id) != ADMIN_ID: return
    text = (f"⚙️ Admin Panel\n\n👥 Total Users: {len(users_db)}\n\n📢 Current Channel: @{MAIN_CHANNEL}\n\n👉 /broadcast [Message] - Sabhi ko message bhejein\n👉 /view_tasks - Task Proofs check karein ✅\n👉 /view_withdraws - Withdraw requests")
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if str(message.from_user.id) != ADMIN_ID: return
    text_split = message.text.split(maxsplit=1)
    if len(text_split) < 2: return bot.send_message(message.chat.id, "❌ Format: /broadcast Hello")
    broadcast_msg = text_split[1]
    success_count = 0
    for user_id in users_db.keys():
        try:
            bot.send_message(user_id, f"📢 ANNOUNCEMENT:\n\n{broadcast_msg}")
            success_count += 1
        except: continue
    bot.send_message(message.chat.id, f"✅ Broadcast Complete! {success_count} users tak pahoncha.")

@bot.message_handler(commands=['view_tasks'])
def view_tasks(message):
    if str(message.from_user.id) != ADMIN_ID: return
    if not task_requests: return bot.send_message(message.chat.id, "📁 Koi naya task proof pending nahi hai.")
    for req in task_requests:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Approve ✅", callback_data=f"app_t_{req['id']}"), telebot.types.InlineKeyboardButton("Reject ❌", callback_data=f"rej_t_{req['id']}"))
        bot.send_photo(message.chat.id, req['photo_id'], caption=f"📝 Task Proof!\n\nUser ID: {req['user_id']}\nType: {req['type'].upper()}\nReward: ₹{req['bonus']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('app_t_', 'rej_t_')))
def handle_task_action(call):
    action, _, req_id = call.data.partition('_t_')
    req = next((r for r in task_requests if r['id'] == req_id), None)
    if not req: return
    if action == "app":
        users_db[req['user_id']]['balance'] += req['bonus']
        users_db[req['user_id']]['tasks'][req['type']] = True
        bot.send_message(req['user_id'], f"✅ Task Approved!\nAapka {req['type'].upper()} task sahi paya gaya. ₹{req['bonus']} aapke wallet me add kar diye gaye hain.")
        bot.edit_message_caption(f"✅ Approved: {req['user_id']} | Type: {req['type'].upper()}", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(req['user_id'], f"❌ Task Rejected!\nAapka submitted screenshot galat ya nakli tha. Kripya sahi se task karke dubara submit karein.")
        bot.edit_message_caption(f"❌ Rejected: {req['user_id']} | Type: {req['type'].upper()}", call.message.chat.id, call.message.message_id)
    task_requests.remove(req)

@bot.message_handler(commands=['view_withdraws'])
def view_withdraws(message):
    if str(message.from_user.id) != ADMIN_ID: return
    if not withdraw_requests: return bot.send_message(message.chat.id, "📁 Pending withdraw requests nahi hain.")
    for req in withdraw_requests:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Approve / Paid ✅", callback_data=f"pay_w_{req['id']}"), telebot.types.InlineKeyboardButton("Reject ❌", callback_data=f"rej_w_{req['id']}"))
        bot.send_message(message.chat.id, f"💰 Withdraw Request!\n\n👤 User: {req['user_id']}\n💵 Amount: ₹{req['amount']}\n🆔 UPI ID: {req['upi']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('pay_w_', 'rej_w_')))
def handle_withdraw_action(call):
    action, _, req_id = call.data.partition('_w_')
    req = next((r for r in withdraw_requests if r['id'] == req_id), None)
    if not req: return
    if action == "pay":
        bot.send_message(req['user_id'], f"✅ Withdraw Approved!\nAapka ₹{req['amount']} aapke UPI ID ({req['upi']}) par bhej diya gaya hai.")
        bot.edit_message_text(f"✅ Paid: {req['user_id']} | Amount: ₹{req['amount']}", call.message.chat.id, call.message.message_id)
    else:
        users_db[req['user_id']]['balance'] += req['amount']
        bot.send_message(req['user_id'], f"❌ Withdraw Rejected! Wallet me paise wapas bhej diye gaye hain.")
        bot.edit_message_text(f"❌ Rejected: {req['user_id']}", call.message.chat.id, call.message.message_id)
    withdraw_requests.remove(req)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    if not check_join(user_id): return start(message)
    if user_id in users_db and 'tasks' not in users_db[user_id]:
        users_db[user_id]['tasks'] = {'tg': False, 'yt': False}

    if message.text == "📊 My Profile":
        u = users_db.get(user_id, {'balance': 0, 'ref_count': 0})
        bot.send_message(message.chat.id, f"👤 Profile Details\n\n💰 Balance: ₹{u['balance']}\n👥 Total Refers: {u['ref_count']}")
    elif message.text == "🔗 Refer & Earn":
        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(message.chat.id, f"🎁 Refer & Earn System\n\nHar ek dost ko join karwane pe aapko ₹{REFER_BONUS} milenge jaise hi wo channel join karega!\n\n🔗 Your Refer Link:\n{link}")
    elif message.text == "💰 Earning Tasks 🚀":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔹 Join Telegram Channel (₹2)", callback_data="task_tg"))
        markup.add(telebot.types.InlineKeyboardButton("🔺 Subscribe YouTube Channel (₹3)", callback_data="task_yt"))
        bot.send_message(message.chat.id, "🎯 Extra Cash Tasks\n\nNiche diye gaye tasks poore karke aap aur zyada paise kama sakte hain. Har task ka proof (screenshot) dena zaroori hai:", reply_markup=markup)
    elif message.text == "📞 Support":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{SUPPORT_USERNAME}"))
        bot.send_message(message.chat.id, "🛠️ Support\n\nAdmin se baat karne ke liye niche click karein.", reply_markup=markup)
    elif message.text == "💰 Withdraw Money":
        bal = users_db.get(user_id, {'balance': 0})['balance']
        if bal < MIN_WITHDRAW: return bot.send_message(message.chat.id, f"❌ Minimum limit ₹{MIN_WITHDRAW} hai.")
        msg = bot.send_message(message.chat.id, "✍️ Format me likhein: UPI_ID | Amount (Example: bhai@upi | 25)")
        bot.register_next_step_handler(msg, process_withdraw)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('task_tg', 'task_yt')))
def handle_task_buttons(call):
    user_id = str(call.from_user.id)
    task_type = "tg" if "tg" in call.data else "yt"
    if users_db[user_id]['tasks'].get(task_type, False):
        return bot.answer_callback_query(call.id, "❌ Aap yeh task pehle hi poora kar chuke hain!", show_alert=True)
    if task_type == "tg":
        url = f"https://t.me/{MAIN_CHANNEL}"
        text = f"📢 Telegram Task\n\n1. Niche diye gaye channel ko join karein:\n👉 {url}\n\n2. Join karne ke baad ek Screenshot lein.\n3. Is chat me wo screenshot bhejien (As a Photo)."
    else:
        url = YOUTUBE_LINK
        text = f"🔺 YouTube Task\n\n1. Niche diye gaye link par jaakar channel ko Subscribe karein:\n👉 {url}\n\n2. Subscribe karne ke baad ek Screenshot lein.\n3. Is chat me wo screenshot bhejien (As a Photo)."
    bot.delete_message(call.message.chat.id, call.message.message_id)
    msg = bot.send_message(call.message.chat.id, text)
    bot.register_next_step_handler(msg, lambda m: process_task_proof(m, task_type))

def process_task_proof(message, task_type):
    user_id = str(message.from_user.id)
    if not message.photo:
        return bot.send_message(message.chat.id, "❌ Aapne photo nahi bheji! Dobara 'Earning Tasks' me jaakar sahi se photo submit karein.")
    photo_id = message.photo[-1].file_id
    bonus = TELEGRAM_TASK_BONUS if task_type == "tg" else YOUTUBE_TASK_BONUS
    r_id = str(len(task_requests) + 1)
    task_requests.append({'id': r_id, 'user_id': user_id, 'type': task_type, 'photo_id': photo_id, 'bonus': bonus})
    bot.send_message(message.chat.id, "✅ Proof Sent! Admin aapka screenshot verify karke 24 ghante me aapke paise credit kar dega.")
    try: bot.send_message(ADMIN_ID, f"🔔 Naya Task Proof aaya hai! Check karne ke liye /view_tasks type karein.")
    except: pass

def process_withdraw(message):
    try:
        parts = message.text.split('|')
        upi = parts[0].strip()
        amt = int(parts[1].strip())
        user_id = str(message.from_user.id)
        if users_db.get(user_id, {'balance': 0})['balance'] < amt: return bot.send_message(message.chat.id, "❌ Insufficient Balance!")
        users_db[user_id]['balance'] -= amt
        r_id = str(len(withdraw_requests) + 1)
        withdraw_requests.append({'id': r_id, 'user_id': user_id, 'upi': upi, 'amount': amt})
        bot.send_message(message.chat.id, f"✅ Request Sent!")
        try: bot.send_message(ADMIN_ID, f"🔔 Nayi Withdraw Request! /view_withdraws")
        except: pass
    except: bot.send_message(message.chat.id, "❌ Format error!")

if __name__ == '__main__':
    keep_alive()  # Fake server chalu karega taaki Render timeout na kare
    bot.infinity_polling()
    
