from telebot import TeleBot, types
from datetime import datetime, timedelta
import json
from typing import Dict, Optional
from ..config.settings import PREMIUM_PRICES, USER_LIMITS
from ..utils.database import Database
from ..utils.logger import Logger

class PremiumHandler:
    def __init__(self, bot: TeleBot, db: Database, logger: Logger):
        self.bot = bot
        self.db = db
        self.logger = logger
        self.pending_payments: Dict[int, dict] = {}
        self.referral_rewards = {
            1: "3_days",
            5: "7_days",
            10: "15_days",
            25: "30_days"
        }
        self._setup_handlers()

    def _setup_handlers(self):
        @self.bot.message_handler(commands=['premium'])
        def premium_info(message):
            markup = types.InlineKeyboardMarkup(row_width=1)
            durations = {
                "1 Month": "1_month",
                "3 Months (15% OFF)": "3_months",
                "6 Months (25% OFF)": "6_months",
                "1 Year (35% OFF)": "12_months"
            }
            
            buttons = []
            for label, duration in durations.items():
                price = self._calculate_price(duration)
                buttons.append(
                    types.InlineKeyboardButton(
                        f"{label} - {price} TON",
                        callback_data=f"premium_{duration}"
                    )
                )
            
            markup.add(*buttons)
            markup.add(types.InlineKeyboardButton("💎 Benefits", callback_data="premium_benefits"))
            
            self.bot.reply_to(
                message,
                "🌟 Premium Subscription Options:\n\n"
                "Choose your subscription duration:",
                reply_markup=markup
            )

    def _calculate_price(self, duration: str) -> float:
        if duration not in PREMIUM_PRICES:
            return 0.0
            
        price = PREMIUM_PRICES[duration]['price']
        discount = PREMIUM_PRICES[duration]['discount']
        return price * (1 - discount/100)

    def process_payment(self, user_id: int, duration: str) -> bool:
        try:
            price = self._calculate_price(duration)
            payment_data = {
                'user_id': user_id,
                'amount': price,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            self.pending_payments[user_id] = payment_data
            
            # Generate payment options markup
            markup = types.InlineKeyboardMarkup(row_width=1)
            buttons = [
                types.InlineKeyboardButton("💎 Pay with TON", callback_data=f"pay_ton_{duration}"),
                types.InlineKeyboardButton("⭐ Pay with Telegram Stars", callback_data=f"pay_stars_{duration}"),
                types.InlineKeyboardButton("🏦 Bank Transfer", callback_data=f"pay_bank_{duration}"),
                types.InlineKeyboardButton("💳 Credit Card (Coming Soon)", callback_data="pay_card_soon")
            ]
            markup.add(*buttons)
            
            self.bot.send_message(
                user_id,
                f"Total Amount: {price} TON\n"
                f"Duration: {duration.replace('_', ' ').title()}\n\n"
                "Choose your payment method:",
                reply_markup=markup
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Payment processing error: {str(e)}")
            return False

    def check_premium_status(self, user_id: int) -> bool:
        """Check if user has active premium subscription"""
        try:
            user_data = self.db.get_user(user_id)
            if not user_data or not user_data.get('is_premium'):
                return False
                
            expiry_date = datetime.fromisoformat(user_data.get('premium_expiry', ''))
            return expiry_date > datetime.now()
            
        except Exception as e:
            self.logger.error(f"Premium status check error: {str(e)}")
            return False

    def process_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Process referral rewards"""
        try:
            referral_count = self.db.get_user_referrals(referrer_id)
            
            for count, reward in self.referral_rewards.items():
                if referral_count == count:
                    days = int(reward.split('_')[0])
                    self.extend_premium(referrer_id, days)
                    self.bot.send_message(
                        referrer_id,
                        f"🎁 You've received {days} days of premium for referring {count} users!"
                    )
                    
            self.db.add_referral(referrer_id, referred_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Referral processing error: {str(e)}")
            return False

    def extend_premium(self, user_id: int, days: int) -> bool:
        """Extend premium subscription by specified days"""
        try:
            user_data = self.db.get_user(user_id)
            current_expiry = datetime.fromisoformat(
                user_data.get('premium_expiry', datetime.now().isoformat())
            )
            
            if not self.check_premium_status(user_id):
                current_expiry = datetime.now()
                
            new_expiry = current_expiry + timedelta(days=days)
            self.db.update_user_premium_status(user_id, True, new_expiry)
            return True
            
        except Exception as e:
            self.logger.error(f"Premium extension error: {str(e)}")
            return False

    def get_premium_features(self, user_id: int) -> dict:
        """Get available premium features for user"""
        is_premium = self.check_premium_status(user_id)
        return USER_LIMITS['premium'] if is_premium else USER_LIMITS['normal']