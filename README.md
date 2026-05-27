# Telegram OTP Sale Bot

A Telegram bot for selling OTP (One-Time Password) codes and services with 24/7 hosting support.

## Features

### User Features
- 📱 Sell OTP packages (1, 5, 10, unlimited)
- 🛒 Browse and purchase additional services
- � Add funds via USDT with QR code
- � Crypto payment integration (USDT, BTC)
- 🔐 Secure OTP generation
- ⚡ Instant delivery
- 📊 View stock information
- 💳 Check balance and purchased items

### Admin Features
- 📊 Admin dashboard with detailed stats
- ➕ Add custom services with pricing
- 💳 Set USDT payment address
- ₿ Set BTC payment address
- 📦 Manage OTP stock levels
- 📢 Broadcast messages to all users
- 💰 Sales tracking and revenue analytics
- 🖼️ QR code generation for payments

## Pricing

- 1 OTP: $5
- 5 OTPs: $20
- 10 OTPs: $35
- Unlimited: $100

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the bot:
```bash
python bot.py
```

## 24/7 Hosting with Render (Free)

### Option 1: Using render.yaml (Recommended)

1. Create a GitHub repository and push your code
2. Go to [render.com](https://render.com) and sign up
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and deploy

### Option 2: Manual Setup

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: telegram-otp-bot
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: Free
5. Add Environment Variables:
   - `BOT_TOKEN`: 7877065424:AAF7AoN0g62kVrOeBf5d6C8EjCL8X1aAvMQ
   - `ADMIN_ID`: 7317989292
6. Click "Deploy"

## Admin Commands

- `/admin` - Open admin panel with all management options
- `/stats` - View bot statistics (users, sales, revenue, services, stock)
- `/addservice` - Add a new service (interactive wizard)
- `/setusdt <address>` - Set USDT payment address
- `/setbtc <address>` - Set BTC payment address
- `/setstock <count>` - Set OTP stock count
- `/broadcast <message>` - Send message to all users

## Bot Commands

- `/start` - Start the bot and see main menu

## Notes

- The bot uses a JSON file (`bot_data.json`) to store user data
- OTPs are valid for 24 hours
- Payment verification is simulated - integrate with real payment gateway for production
- QR codes are automatically generated for USDT payments
- Admin ID: 7317989292
- Services can be added dynamically through the admin panel

## Security

- Never share your bot token
- Keep admin ID secure
- Use environment variables for sensitive data
- The `.gitignore` file prevents data files from being committed

## Troubleshooting

If the bot doesn't respond:
1. Check the bot token is correct
2. Verify the bot is running
3. Check Render logs for errors
4. Ensure the bot has been started in Telegram by sending `/start`

## Support

For issues or questions, contact the admin.
