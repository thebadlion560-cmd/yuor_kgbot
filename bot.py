import os
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import json
from pathlib import Path
import qrcode
from io import BytesIO

# Configuration
BOT_TOKEN = "7877065424:AAF7AoN0g62kVrOeBf5d6C8EjCL8X1aAvMQ"
ADMIN_ID = 7317989292

# Storage
DATA_FILE = "bot_data.json"

# Pricing
OTP_PRICES = {
    "1": 5,      # $5 for 1 OTP
    "5": 20,     # $20 for 5 OTPs
    "10": 35,    # $35 for 10 OTPs
    "unlimited": 100  # $100 for unlimited
}

# Conversation states
ADD_SERVICE_NAME, ADD_SERVICE_PRICE, ADD_SERVICE_DESC = range(3)
SET_USDT_ADDRESS = range(1)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "users": {},
        "sales": {},
        "otps": {},
        "services": {},
        "usdt_address": "",
        "qr_code": "",
        "stock": {"otp": 1000}
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton("📱 Buy OTP", callback_data="buy_otp")],
        [InlineKeyboardButton("� Services", callback_data="services")],
        [InlineKeyboardButton("� Add Funds", callback_data="add_funds")],
        [InlineKeyboardButton("📊 Stock Info", callback_data="stock_info")],
        [InlineKeyboardButton("💳 My Balance", callback_data="balance")],
        [InlineKeyboardButton("� My OTPs", callback_data="my_otps")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
🤖 **Welcome to OTP Sale Bot!**

🔐 Get secure OTPs for verification
🛒 Browse our services
💳 Simple pricing
⚡ Instant delivery

Click below to get started!
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = query.from_user.id
    
    if query.data == "buy_otp":
        keyboard = [
            [InlineKeyboardButton("1 OTP - $5", callback_data="buy_1")],
            [InlineKeyboardButton("5 OTPs - $20", callback_data="buy_5")],
            [InlineKeyboardButton("10 OTPs - $35", callback_data="buy_10")],
            [InlineKeyboardButton("Unlimited - $100", callback_data="buy_unlimited")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💳 **Choose OTP Package:**", parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data.startswith("buy_"):
        package = query.data.split("_")[1]
        price = OTP_PRICES[package]
        
        keyboard = [
            [InlineKeyboardButton("💳 Crypto Payment", callback_data=f"pay_crypto_{package}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="buy_otp")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"💰 **Payment: ${price}**\n\nChoose payment method:", parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data.startswith("pay_crypto_"):
        package = query.data.split("_")[2]
        price = OTP_PRICES[package]
        
        # Generate payment address (simplified - in production use real payment gateway)
        payment_address = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        
        keyboard = [
            [InlineKeyboardButton("✅ I've Paid", callback_data=f"confirm_pay_{package}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="buy_otp")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💳 **Crypto Payment**\n\n"
            f"Amount: ${price}\n"
            f"Send BTC to: `{payment_address}`\n\n"
            f"⚠️ Send exact amount\n"
            f"Click 'I've Paid' after sending",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data.startswith("confirm_pay_"):
        package = query.data.split("_")[2]
        
        # Simulate payment confirmation (in production, verify with blockchain)
        data = load_data()
        
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {"balance": 0, "otps": []}
        
        # Add OTPs to user
        if package == "unlimited":
            data["users"][str(user_id)]["unlimited"] = True
            data["users"][str(user_id)]["otps"] = ["UNLIMITED"]
        else:
            count = int(package)
            for _ in range(count):
                otp = generate_otp()
                expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                data["users"][str(user_id)]["otps"].append({"code": otp, "expiry": expiry})
        
        # Record sale
        if str(user_id) not in data["sales"]:
            data["sales"][str(user_id)] = []
        data["sales"][str(user_id)].append({
            "package": package,
            "price": OTP_PRICES[package],
            "date": datetime.now().isoformat()
        })
        
        save_data(data)
        
        keyboard = [
            [InlineKeyboardButton("📱 View OTPs", callback_data="my_otps")],
            [InlineKeyboardButton("🏠 Home", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ **Payment Confirmed!**\n\nYour OTPs have been added to your account.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == "balance":
        data = load_data()
        user_data = data["users"].get(str(user_id), {"balance": 0, "otps": []})
        await query.edit_message_text(f"💰 **Your Balance:** ${user_data['balance']}", parse_mode='Markdown')
    
    elif query.data == "my_otps":
        data = load_data()
        user_data = data["users"].get(str(user_id), {"balance": 0, "otps": []})
        
        if user_data.get("unlimited"):
            otps_text = "🔓 **UNLIMITED ACCESS**\n\nClick 'Generate OTP' to get a new code anytime."
            keyboard = [
                [InlineKeyboardButton("🔄 Generate OTP", callback_data="generate_otp")],
                [InlineKeyboardButton("🏠 Home", callback_data="back")]
            ]
        elif user_data["otps"]:
            otps_text = "📱 **Your OTPs:**\n\n"
            for i, otp in enumerate(user_data["otps"][:5], 1):
                if isinstance(otp, dict):
                    expiry = datetime.fromisoformat(otp["expiry"])
                    remaining = (expiry - datetime.now()).total_seconds() / 3600
                    otps_text += f"{i}. `{otp['code']}` - {remaining:.1f}h remaining\n"
                else:
                    otps_text += f"{i}. {otp}\n"
            
            if len(user_data["otps"]) > 5:
                otps_text += f"\n... and {len(user_data['otps']) - 5} more"
            
            keyboard = [
                [InlineKeyboardButton("🏠 Home", callback_data="back")]
            ]
        else:
            otps_text = "❌ You have no OTPs. Purchase some to get started!"
            keyboard = [
                [InlineKeyboardButton("💳 Buy OTP", callback_data="buy_otp")],
                [InlineKeyboardButton("🏠 Home", callback_data="back")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(otps_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == "generate_otp":
        data = load_data()
        user_data = data["users"].get(str(user_id), {})
        
        if user_data.get("unlimited"):
            new_otp = generate_otp()
            await query.edit_message_text(f"🔐 **New OTP Generated:**\n\n`{new_otp}`\n\nValid for 24 hours", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ You don't have unlimited access.")
    
    elif query.data == "help":
        help_text = """
❓ **Help & FAQ**

📱 **What is OTP?**
One-Time Password for secure verification

💳 **How to buy?**
1. Click 'Buy OTP'
2. Choose package
3. Make payment
4. Receive OTPs instantly

⚡ **Features**
- Instant delivery
- 24-hour validity
- Secure codes

👨‍💻 **Need help?**
Contact admin: @admin
"""
        keyboard = [
            [InlineKeyboardButton("🏠 Home", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("📱 Buy OTP", callback_data="buy_otp")],
            [InlineKeyboardButton("� Services", callback_data="services")],
            [InlineKeyboardButton("� Add Funds", callback_data="add_funds")],
            [InlineKeyboardButton("📊 Stock Info", callback_data="stock_info")],
            [InlineKeyboardButton("💳 My Balance", callback_data="balance")],
            [InlineKeyboardButton("� My OTPs", callback_data="my_otps")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🤖 **Main Menu**", parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == "services":
        data = load_data()
        services = data.get("services", {})
        
        if services:
            services_text = "🛒 **Available Services:**\n\n"
            keyboard = []
            for service_id, service in services.items():
                services_text += f"• {service['name']} - ${service['price']}\n"
                keyboard.append([InlineKeyboardButton(f"{service['name']} - ${service['price']}", callback_data=f"buy_service_{service_id}")])
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(services_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ No services available at the moment.", reply_markup=reply_markup)
    
    elif query.data.startswith("buy_service_"):
        service_id = query.data.split("_")[2]
        data = load_data()
        service = data["services"].get(service_id)
        
        if service:
            keyboard = [
                [InlineKeyboardButton("💳 USDT Payment", callback_data=f"pay_usdt_{service_id}")],
                [InlineKeyboardButton("💳 BTC Payment", callback_data=f"pay_btc_{service_id}")],
                [InlineKeyboardButton("⬅️ Back", callback_data="services")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🛒 **{service['name']}**\n\n"
                f"Price: ${service['price']}\n"
                f"{service.get('description', '')}\n\n"
                f"Choose payment method:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    elif query.data.startswith("pay_usdt_"):
        service_id = query.data.split("_")[2]
        data = load_data()
        service = data["services"].get(service_id)
        usdt_address = data.get("usdt_address", "TYourUSDTAddressHere")
        
        # Generate QR code
        qr = qrcode.make(usdt_address)
        qr_buffer = BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        keyboard = [
            [InlineKeyboardButton("✅ I've Paid", callback_data=f"confirm_service_pay_{service_id}")],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"buy_service_{service_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_photo(
            photo=qr_buffer,
            caption=f"💳 **USDT Payment**\n\n"
                   f"Amount: ${service['price']}\n"
                   f"Address: `{usdt_address}`\n\n"
                   f"⚠️ Send exact amount\n"
                   f"Click 'I've Paid' after sending",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        await query.delete_message()
    
    elif query.data.startswith("pay_btc_"):
        service_id = query.data.split("_")[2]
        data = load_data()
        service = data["services"].get(service_id)
        btc_address = data.get("btc_address", "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh")
        
        keyboard = [
            [InlineKeyboardButton("✅ I've Paid", callback_data=f"confirm_service_pay_{service_id}")],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"buy_service_{service_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💳 **BTC Payment**\n\n"
            f"Amount: ${service['price']}\n"
            f"Address: `{btc_address}`\n\n"
            f"⚠️ Send exact amount\n"
            f"Click 'I've Paid' after sending",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data.startswith("confirm_service_pay_"):
        service_id = query.data.split("_")[3]
        data = load_data()
        service = data["services"].get(service_id)
        
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {"balance": 0, "otps": []}
        
        # Add service to user's purchased services
        if "purchased_services" not in data["users"][str(user_id)]:
            data["users"][str(user_id)]["purchased_services"] = []
        data["users"][str(user_id)]["purchased_services"].append({
            "service_id": service_id,
            "name": service['name'],
            "date": datetime.now().isoformat()
        })
        
        # Record sale
        if str(user_id) not in data["sales"]:
            data["sales"][str(user_id)] = []
        data["sales"][str(user_id)].append({
            "service": service['name'],
            "price": service['price'],
            "date": datetime.now().isoformat()
        })
        
        save_data(data)
        
        keyboard = [
            [InlineKeyboardButton("🏠 Home", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ **Payment Confirmed!**\n\nYou have purchased: {service['name']}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == "add_funds":
        keyboard = [
            [InlineKeyboardButton("$10", callback_data="add_fund_10")],
            [InlineKeyboardButton("$25", callback_data="add_fund_25")],
            [InlineKeyboardButton("$50", callback_data="add_fund_50")],
            [InlineKeyboardButton("$100", callback_data="add_fund_100")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💰 **Select Amount to Add:**", parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data.startswith("add_fund_"):
        amount = query.data.split("_")[2]
        data = load_data()
        usdt_address = data.get("usdt_address", "TYourUSDTAddressHere")
        
        # Generate QR code
        qr = qrcode.make(usdt_address)
        qr_buffer = BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        keyboard = [
            [InlineKeyboardButton("✅ I've Paid", callback_data=f"confirm_fund_{amount}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="add_funds")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_photo(
            photo=qr_buffer,
            caption=f"💰 **Add Funds**\n\n"
                   f"Amount: ${amount}\n"
                   f"USDT Address: `{usdt_address}`\n\n"
                   f"⚠️ Send exact amount\n"
                   f"Click 'I've Paid' after sending",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        await query.delete_message()
    
    elif query.data.startswith("confirm_fund_"):
        amount = int(query.data.split("_")[2])
        data = load_data()
        
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {"balance": 0, "otps": []}
        
        data["users"][str(user_id)]["balance"] += amount
        
        save_data(data)
        
        keyboard = [
            [InlineKeyboardButton("🏠 Home", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ **Funds Added!**\n\nYour new balance: ${data['users'][str(user_id)]['balance']}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == "stock_info":
        data = load_data()
        stock = data.get("stock", {"otp": 1000})
        
        stock_text = f"""
📊 **Stock Information**

📱 OTP Available: {stock.get('otp', 0)}
🔄 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

💡 Stock updates automatically
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="stock_info")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(stock_text, parse_mode='Markdown', reply_markup=reply_markup)

# Admin commands
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("➕ Add Service", callback_data="admin_add_service")],
        [InlineKeyboardButton("💳 Set USDT Address", callback_data="admin_set_usdt")],
        [InlineKeyboardButton("₿ Set BTC Address", callback_data="admin_set_btc")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📦 Manage Stock", callback_data="admin_stock")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("🔧 **Admin Panel**", parse_mode='Markdown', reply_markup=reply_markup)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    data = load_data()
    total_users = len(data["users"])
    total_sales = sum(len(sales) for sales in data["sales"].values())
    total_revenue = sum(
        sum(sale["price"] for sale in sales)
        for sales in data["sales"].values()
    )
    
    stats = f"""
📊 **Admin Stats**

👥 Total Users: {total_users}
💰 Total Sales: {total_sales}
💵 Total Revenue: ${total_revenue}
🛒 Services: {len(data.get('services', {}))}
📦 OTP Stock: {data.get('stock', {}).get('otp', 0)}
"""
    await update.message.reply_text(stats, parse_mode='Markdown')

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    data = load_data()
    
    sent = 0
    for user_id in data["users"]:
        try:
            await context.bot.send_message(chat_id=int(user_id), text=message)
            sent += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")

# Admin conversation handlers
async def add_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return ConversationHandler.END
    
    await update.message.reply_text("📝 Enter service name:")
    return ADD_SERVICE_NAME

async def add_service_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['service_name'] = update.message.text
    await update.message.reply_text("💰 Enter service price (in USD):")
    return ADD_SERVICE_PRICE

async def add_service_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text)
        context.user_data['service_price'] = price
        await update.message.reply_text("📝 Enter service description (or send /skip to skip):")
        return ADD_SERVICE_DESC
    except ValueError:
        await update.message.reply_text("❌ Invalid price. Enter a number:")
        return ADD_SERVICE_PRICE

async def add_service_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/skip":
        description = ""
    else:
        description = update.message.text
    
    data = load_data()
    service_id = str(len(data.get("services", {})) + 1)
    
    if "services" not in data:
        data["services"] = {}
    
    data["services"][service_id] = {
        "name": context.user_data['service_name'],
        "price": context.user_data['service_price'],
        "description": description
    }
    
    save_data(data)
    
    await update.message.reply_text(f"✅ Service '{context.user_data['service_name']}' added successfully!")
    return ConversationHandler.END

async def set_usdt_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /setusdt <address>")
        return
    
    address = context.args[0]
    data = load_data()
    data["usdt_address"] = address
    save_data(data)
    
    await update.message.reply_text("✅ USDT address updated!")

async def set_btc_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /setbtc <address>")
        return
    
    address = context.args[0]
    data = load_data()
    data["btc_address"] = address
    save_data(data)
    
    await update.message.reply_text("✅ BTC address updated!")

async def set_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /setstock <otp_count>")
        return
    
    try:
        count = int(context.args[0])
        data = load_data()
        if "stock" not in data:
            data["stock"] = {}
        data["stock"]["otp"] = count
        save_data(data)
        await update.message.reply_text(f"✅ OTP stock updated to {count}!")
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Usage: /setstock <otp_count>")

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_stats":
        data = load_data()
        total_users = len(data["users"])
        total_sales = sum(len(sales) for sales in data["sales"].values())
        total_revenue = sum(
            sum(sale["price"] for sale in sales)
            for sales in data["sales"].values()
        )
        
        stats = f"""
📊 **Admin Stats**

👥 Total Users: {total_users}
💰 Total Sales: {total_sales}
💵 Total Revenue: ${total_revenue}
🛒 Services: {len(data.get('services', {}))}
📦 OTP Stock: {data.get('stock', {}).get('otp', 0)}
"""
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(stats, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == "admin_add_service":
        await query.delete_message()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="📝 Enter service name:"
        )
        return ADD_SERVICE_NAME
    
    elif query.data == "admin_set_usdt":
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        data = load_data()
        current = data.get("usdt_address", "Not set")
        await query.edit_message_text(
            f"💳 Current USDT Address: `{current}`\n\nUse /setusdt <address> to update",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == "admin_set_btc":
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        data = load_data()
        current = data.get("btc_address", "Not set")
        await query.edit_message_text(
            f"₿ Current BTC Address: `{current}`\n\nUse /setbtc <address> to update",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == "admin_broadcast":
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📢 Use /broadcast <message> to send a broadcast",
            reply_markup=reply_markup
        )
    
    elif query.data == "admin_stock":
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        data = load_data()
        current = data.get("stock", {}).get("otp", 0)
        await query.edit_message_text(
            f"📦 Current OTP Stock: {current}\n\nUse /setstock <count> to update",
            reply_markup=reply_markup
        )
    
    elif query.data == "admin_panel":
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("➕ Add Service", callback_data="admin_add_service")],
            [InlineKeyboardButton("💳 Set USDT Address", callback_data="admin_set_usdt")],
            [InlineKeyboardButton("₿ Set BTC Address", callback_data="admin_set_btc")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📦 Manage Stock", callback_data="admin_stock")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔧 **Admin Panel**", parse_mode='Markdown', reply_markup=reply_markup)

def main():
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for adding services
    add_service_conv = ConversationHandler(
        entry_points=[CommandHandler("addservice", add_service_start)],
        states={
            ADD_SERVICE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_name)],
            ADD_SERVICE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_price)],
            ADD_SERVICE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_desc)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("setusdt", set_usdt_address))
    app.add_handler(CommandHandler("setbtc", set_btc_address))
    app.add_handler(CommandHandler("setstock", set_stock))
    app.add_handler(add_service_conv)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^admin_"))
    
    # Start bot
    print("🤖 Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
