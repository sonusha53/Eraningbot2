import os
import telebot

# ==================== AAPKI INITIAL DETAILS ====================
# 1. Apne BotFather wale bot ka Token yahan daalein
BOT_TOKEN = "8984080434:AAHn0dvGU4FOumJhfRFXzk2-FWHtELq4eQg"
bot = telebot.TeleBot(BOT_TOKEN)

# 2. Aapki Telegram Account ID (Admin ID)
ADMIN_ID = "8063553847"        

# 3. Aapke Bot ka Username bina '@' ke (Example: SonuEarningBot)
# ISSE SAHI SE LIKHNA TAAKI REFER LINK 100% SAHI BANE
BOT_USERNAME = "Apne_Bot_Ka_Username_Yahan_Likho"  

# 4. Aapka Support ya Personal Username bina '@' ke
SUPPORT_USERNAME = "gainoffiicialnick"  
# ===============================================================

# Sirf 1 main channel jo join karna zaroori hai (Bina @ ke)
MAIN_CHANNEL = "eraningwithask9" 

REFER_BONUS = 7
MIN_WITHDRAW = 20

users_db = {}
withdraw_requests = []

def check_join(user_id):
    """Check karta hai ki user ne channel join kiya hai ya nahi"""
    try:
        member = bot.get_chat_member(f"@{MAIN_CHANNEL}", int(user_id))
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        # Agar bot channel me admin nahi hai toh user ko bypass kar dega taaki bot crash na ho
        return True

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    
    if user_id not in users_db:
        users_db[user_id] = {'balance': 0, 'referred_by': None, 'ref_count': 0, 'joined': False}
        
        # Refer link tracking system
        text_split = message.text.split()
        if len(text_split) > 1:
            referrer_id = text_split[1]
            if referrer_id != user_id and referrer_id in users_db:
                users_db[user_id]['referred_by'] = referrer_id

    # Force Join Check
    if not check_join(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="📢 Join Channel", url=f"https://t.me/{MAIN_CHANNEL}"))
        markup.add(telebot.types.InlineKeyboardButton(text="✅ Joined / Verify", callback_data="verify_join"))
        
        bot.send_message(
            message.chat.id, 
            f"❌ **Access Denied!**\n\nBot use karne ke liye aapko hamare official channel **@{MAIN_CHANNEL}** ko join karna hoga. Join karke niche diye gaye **Verify** button par click karein:", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    main_menu(message.chat.id, username)

def main_menu(chat_id, username):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 My Profile", "🔗 Refer & Earn")
    markup.add("💰 Withdraw Money", "📞 Support")
    bot.send_message(chat_id, f"👋 **Welcome {username} to Earning Bot!**\n\nYahan aap dosto ko refer karke real cash kama sakte hain.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    user_id = str(call.from_user.id)
    if check_join(user_id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        # Referral bonus add karna
        if users_db.get(user_id) and users_db[user_id]['referred_by'] and not users_db[user_id]['joined']:
            ref_id = users_db[user_id]['referred_by']
            if ref_id in users_db:
                users_db[ref_id]['balance'] += REFER_BONUS
                users_db[ref_id]['ref_count'] += 1
                try: bot.send_message(ref_id, f"🎉 **Naya Referral!** Aapke link se user ne channel join kiya. Aapko **₹{REFER_BONUS}** mile!")
                except: pass
                    
        if user_id in users_db:
            users_db[user_id]['joined'] = True
            
        bot.answer_callback_query(call.id, "✅ Verification Successful!", show_alert=True)
        main_menu(call.message.chat.id, call.from_user.username or "User")
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)

# ==================== ADMIN PANEL ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.from_user.id) != ADMIN_ID: return
    text = f"⚙️ **Admin Panel**\n\n👥 **Total Users:** {len(users_db)}\n\n📢 **Current Channel:** @{MAIN_CHANNEL}\n\n👉 **Channel badalne ke liye:**\n`/setchannel [username]`\n\n👉 **Withdraw requests dekhne ke liye:** /view_withdraws"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['setchannel'])
def set_channel_cmd(message):
    global MAIN_CHANNEL
    if str(message.from_user.id) != ADMIN_ID: return
    try:
        parts = message.text.split()
        new_user = parts[1].replace("@", "").strip()
        MAIN_CHANNEL = new_user
        bot.send_message(message.chat.id, f"✅ **Main Channel Update Ho Gaya!**\nNaya channel **@{new_user}** set ho gaya hai.")
    except:
        bot.send_message(message.chat.id, "❌ Use: `/setchannel [new_username]`")

@bot.message_handler(commands=['view_withdraws'])
def view_withdraws(message):
    if str(message.from_user.id) != ADMIN_ID: return
    if not withdraw_requests: return bot.send_message(message.chat.id, "📁 Pending withdraw requests nahi hain.")
    for req in withdraw_requests:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Approve / Paid ✅", callback_data=f"pay_w_{req['id']}"), telebot.types.InlineKeyboardButton("Reject ❌", callback_data=f"rej_w_{req['id']}"))
        bot.send_message(message.chat.id, f"💰 **Withdraw Request!**\n\n👤 User: `{req['user_id']}`\n💵 Amount: **₹{req['amount']}**\n🆔 UPI ID: `{req['upi']}`", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('pay_w_', 'rej_w_')))
def handle_withdraw_action(call):
    action, _, req_id = call.data.partition('_w_')
    req = next((r for r in withdraw_requests if r['id'] == req_id), None)
    if not req: return
    if action == "pay":
        bot.send_message(req['user_id'], f"✅ **Withdraw Approved!**\nAapka ₹{req['amount']} aapke UPI ID ({req['upi']}) par bhej diya gaya hai.")
        bot.edit_message_text(f"✅ **Paid:** {req['user_id']} | Amount: ₹{req['amount']}", call.message.chat.id, call.message.message_id)
    else:
        users_db[req['user_id']]['balance'] += req['amount']
        bot.send_message(req['user_id'], f"❌ **Withdraw Rejected!** Wallet me paise wapas bhej diye gaye hain.")
        bot.edit_message_text(f"❌ **Rejected:** {req['user_id']}", call.message.chat.id, call.message.message_id)
    withdraw_requests.remove(req)

# ==================== USER FEATURES ====================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    if not check_join(user_id): return start(message)

    if message.text == "📊 My Profile":
        u = users_db.get(user_id, {'balance': 0, 'ref_count': 0})
        bot.send_message(message.chat.id, f"👤 **Profile Details**\n\n💰 Balance: **₹{u['balance']}**\n👥 Total Refers: **{u['ref_count']}**", parse_mode="Markdown")
        
    elif message.text == "🔗 Refer & Earn":
        # Fix: Yahan fixed variable use kiya hai taaki error na aaye
        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(
            message.chat.id, 
            f"🎁 **Refer & Earn System**\n\nHar ek dost ko join karwane pe aapko **₹{REFER_BONUS}** milenge jab wo channel join karega!\n\n🔗 **Your Refer Link:**\n{link}",
            parse_mode="Markdown"
        )
        
    elif message.text == "📞 Support":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{SUPPORT_USERNAME}"))
        bot.send_message(message.chat.id, "🛠️ **Support**\n\nAdmin se baat karne ke liye niche click karein.", reply_markup=markup, parse_mode="Markdown")
        
    elif message.text == "💰 Withdraw Money":
        bal = users_db.get(user_id, {'balance': 0})['balance']
        if bal < MIN_WITHDRAW: return bot.send_message(message.chat.id, f"❌ **Minimum limit ₹{MIN_WITHDRAW} hai.**")
        msg = bot.send_message(message.chat.id, "✍️ Format me likhein: `UPI_ID | Amount` (Example: `bhai@upi | 25`)")
        bot.register_next_step_handler(msg, process_withdraw)

def process_withdraw(message):
    try:
        parts = message.text.split('|')
        upi = parts[0].strip()
        amt = int(parts[1].strip())
        user_id = str(message.from_user.id)
        if users_db.get(user_id, {'balance': 0})['balance'] < amt: return bot.send_message(message.chat.id, "❌ **Insufficient Balance!**")
        users_db[user_id]['balance'] -= amt
        r_id = str(len(withdraw_requests) + 1)
        withdraw_requests.append({'id': r_id, 'user_id': user_id, 'upi': upi, 'amount': amt})
        bot.send_message(message.chat.id, f"✅ **Request Sent!**")
        try: bot.send_message(ADMIN_ID, f"🔔 Nayi Withdraw Request! /view_withdraws")
        except: pass
    except: bot.send_message(message.chat.id, "❌ Format error!")

bot.infinity_polling()
        
