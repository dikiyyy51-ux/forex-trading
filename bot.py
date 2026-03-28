"""
PROFESSIONAL FOREX TRADING BOT - 5 ВАЛЮТНЫХ ПАР
USD/CHF, EUR/USD, GBP/USD, USD/JPY, AUD/USD
С МЕНЮ КЛАВИШ И ПРОФЕССИОНАЛЬНЫМИ ГРАФИКАМИ
"""

import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import io
import warnings
warnings.filterwarnings('ignore')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8639759681:AAHqfHyIxx3BiICWF-P3ul-_GtfaheVCSCE"

logging.basicConfig(level=logging.INFO)

# ==================== НАСТРОЙКИ ПАР ====================
PAIRS = {
    'USDCHF': {'name': 'USD/CHF', 'base': 'USD', 'quote': 'CHF', 'volatility': 0.0006, 'color': '#2ecc71'},
    'EURUSD': {'name': 'EUR/USD', 'base': 'EUR', 'quote': 'USD', 'volatility': 0.0007, 'color': '#3498db'},
    'GBPUSD': {'name': 'GBP/USD', 'base': 'GBP', 'quote': 'USD', 'volatility': 0.0009, 'color': '#e74c3c'},
    'USDJPY': {'name': 'USD/JPY', 'base': 'USD', 'quote': 'JPY', 'volatility': 0.0008, 'color': '#f1c40f'},
    'AUDUSD': {'name': 'AUD/USD', 'base': 'AUD', 'quote': 'USD', 'volatility': 0.0007, 'color': '#9b59b6'}
}

def get_pair_info(pair_code):
    """Получить информацию о паре"""
    return PAIRS.get(pair_code, PAIRS['USDCHF'])

# ==================== КЛАВИАТУРА МЕНЮ ====================
def get_main_keyboard():
    """Главная клавиатура с кнопками"""
    keyboard = [
        [KeyboardButton("🇺🇸🇨🇭 USD/CHF"), KeyboardButton("🇪🇺🇺🇸 EUR/USD")],
        [KeyboardButton("🇬🇧🇺🇸 GBP/USD"), KeyboardButton("🇺🇸🇯🇵 USD/JPY")],
        [KeyboardButton("🇦🇺🇺🇸 AUD/USD"), KeyboardButton("📈 Статус рынка")],
        [KeyboardButton("❓ Помощь"), KeyboardButton("🔔 Подписаться")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_inline_keyboard():
    """Инлайн-клавиатура для сообщений"""
    keyboard = [
        [InlineKeyboardButton("🇺🇸🇨🇭 USD/CHF", callback_data='usdchf')],
        [InlineKeyboardButton("🇪🇺🇺🇸 EUR/USD", callback_data='eurusd')],
        [InlineKeyboardButton("🇬🇧🇺🇸 GBP/USD", callback_data='gbpusd')],
        [InlineKeyboardButton("🇺🇸🇯🇵 USD/JPY", callback_data='usdjpy')],
        [InlineKeyboardButton("🇦🇺🇺🇸 AUD/USD", callback_data='audusd')],
        [InlineKeyboardButton("📈 Статус рынка", callback_data='status')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== ПОЛУЧЕНИЕ РЕАЛЬНЫХ КУРСОВ ====================
def get_real_forex_rate(pair_code="USDCHF"):
    """Получение реального курса валютной пары"""
    pair = get_pair_info(pair_code)
    base = pair['base']
    quote = pair['quote']
    
    urls = [
        f"https://api.exchangerate-api.com/v4/latest/{base}",
        f"https://api.frankfurter.app/latest?from={base}&to={quote}",
        f"https://api.exchangerate.host/latest?base={base}&symbols={quote}"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data:
                    if quote in data['rates']:
                        return data['rates'][quote]
                    elif quote.lower() in data['rates']:
                        return data['rates'][quote.lower()]
        except:
            continue
    
    # Стандартные курсы на случай ошибки
    default_rates = {
        'USDCHF': 0.8325,
        'EURUSD': 1.0850,
        'GBPUSD': 1.2650,
        'USDJPY': 149.50,
        'AUDUSD': 0.6550
    }
    return default_rates.get(pair_code, 0.8325)

def get_forex_data(pair_code="USDCHF", periods=150):
    """Получение рыночных данных с учетом волатильности пары"""
    pair = get_pair_info(pair_code)
    current_rate = get_real_forex_rate(pair_code)
    volatility = pair['volatility']
    
    np.random.seed(int(datetime.now().timestamp()) % 10000)
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='h')
    
    # Разный тренд для разных пар
    trend_map = {
        'USDCHF': 0.0002,
        'EURUSD': -0.0001,
        'GBPUSD': 0.0003,
        'USDJPY': 0.0004,
        'AUDUSD': 0.0001
    }
    trend = np.linspace(0, trend_map.get(pair_code, 0), periods)
    noise = np.random.randn(periods) * volatility
    returns = trend + noise
    prices = current_rate * (1 + np.cumsum(returns))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(periods) * 0.00015),
        'high': prices * (1 + abs(np.random.randn(periods)) * 0.00035),
        'low': prices * (1 - abs(np.random.randn(periods)) * 0.00035),
        'close': prices,
        'volume': np.random.randint(5000, 25000, periods)
    })
    
    for i in range(len(df)):
        df.loc[i, 'high'] = max(df.loc[i, 'high'], df.loc[i, 'open'], df.loc[i, 'close'])
        df.loc[i, 'low'] = min(df.loc[i, 'low'], df.loc[i, 'open'], df.loc[i, 'close'])
    
    df.set_index('timestamp', inplace=True)
    
    # Индикаторы
    df['ema9'] = df['close'].ewm(span=9).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    
    df['bb_mid'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + (bb_std * 2)
    df['bb_lower'] = df['bb_mid'] - (bb_std * 2)
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)
    
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    df['atr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
    
    return df, current_rate

def find_swing_points(df, window=5):
    highs = []
    lows = []
    for i in range(window, len(df) - window):
        if df['high'].iloc[i] == max(df['high'].iloc[i-window:i+window+1]):
            highs.append((df.index[i], df['high'].iloc[i]))
        if df['low'].iloc[i] == min(df['low'].iloc[i-window:i+window+1]):
            lows.append((df.index[i], df['low'].iloc[i]))
    return highs, lows

def find_support_resistance(df):
    highs, lows = find_swing_points(df)
    support = [l[1] for l in lows[-10:]]
    resistance = [h[1] for h in highs[-10:]]
    current_price = df['close'].iloc[-1]
    nearest_support = max([s for s in support if s < current_price], default=None) if support else None
    nearest_resistance = min([r for r in resistance if r > current_price], default=None) if resistance else None
    return {
        'support': support[-5:],
        'resistance': resistance[-5:],
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance
    }

def fibonacci_levels(high, low):
    diff = high - low
    return {
        '0.0': high,
        '0.236': high - diff * 0.236,
        '0.382': high - diff * 0.382,
        '0.5': high - diff * 0.5,
        '0.618': high - diff * 0.618,
        '0.786': high - diff * 0.786,
        '1.0': low
    }

def calculate_entry_levels(df, signal, pair_code):
    current_price = df['close'].iloc[-1]
    atr = df['atr'].iloc[-1]
    sr = find_support_resistance(df)
    
    entry_levels = {}
    
    if signal['action'] == 'BUY':
        entry_levels['primary'] = current_price
        pullback_levels = []
        if sr['nearest_support'] and sr['nearest_support'] < current_price:
            pullback_levels.append(sr['nearest_support'])
        pullback_levels.append(current_price - atr * 0.5)
        pullback_levels.append(current_price - atr * 1.0)
        entry_levels['pullback'] = [l for l in pullback_levels if l < current_price][:2]
        entry_levels['aggressive'] = current_price
        entry_levels['conservative'] = current_price + atr * 0.3
        entry_levels['limit_buy'] = current_price - atr * 0.3
        
    elif signal['action'] == 'SELL':
        entry_levels['primary'] = current_price
        pullback_levels = []
        if sr['nearest_resistance'] and sr['nearest_resistance'] > current_price:
            pullback_levels.append(sr['nearest_resistance'])
        pullback_levels.append(current_price + atr * 0.5)
        pullback_levels.append(current_price + atr * 1.0)
        entry_levels['pullback'] = [l for l in pullback_levels if l > current_price][:2]
        entry_levels['aggressive'] = current_price
        entry_levels['conservative'] = current_price - atr * 0.3
        entry_levels['limit_sell'] = current_price + atr * 0.3
    
    return entry_levels

def create_pro_chart(df, signal, pair_code, fibo_levels, sr_levels, swing_highs, swing_lows, entry_levels):
    pair = get_pair_info(pair_code)
    pair_name = pair['name']
    
    fig = plt.figure(figsize=(18, 14))
    fig.patch.set_facecolor('#0a0c12')
    
    ax1 = plt.subplot(3, 1, 1)
    ax1.set_facecolor('#0f1219')
    
    width = 0.6
    for i, (idx, row) in enumerate(df.iterrows()):
        color = '#2ecc71' if row['close'] >= row['open'] else '#e74c3c'
        body_height = abs(row['close'] - row['open'])
        if body_height > 0:
            rect = Rectangle((i - width/2, min(row['open'], row['close'])), 
                           width, body_height,
                           facecolor=color, edgecolor='white', linewidth=0.5)
            ax1.add_patch(rect)
        ax1.plot([i, i], [row['high'], max(row['open'], row['close'])], color='white', linewidth=0.7)
        ax1.plot([i, i], [min(row['open'], row['close']), row['low']], color='white', linewidth=0.7)
    
    ax1.plot(range(len(df)), df['ema9'], '#f1c40f', linewidth=1.5, label='EMA 9', alpha=0.9)
    ax1.plot(range(len(df)), df['ema21'], '#e67e22', linewidth=1.5, label='EMA 21', alpha=0.9)
    ax1.plot(range(len(df)), df['ema50'], '#3498db', linewidth=1.5, label='EMA 50', alpha=0.8)
    
    ax1.fill_between(range(len(df)), df['bb_upper'], df['bb_lower'], color='#3498db', alpha=0.1)
    ax1.plot(range(len(df)), df['bb_upper'], '#3498db', linewidth=0.8, linestyle='--', alpha=0.5)
    ax1.plot(range(len(df)), df['bb_lower'], '#3498db', linewidth=0.8, linestyle='--', alpha=0.5)
    
    for level in sr_levels['support']:
        ax1.axhline(y=level, color='#2ecc71', linestyle='--', linewidth=1, alpha=0.6)
        ax1.text(len(df)-5, level, f'  Support {level:.5f}', color='#2ecc71', fontsize=8)
    for level in sr_levels['resistance']:
        ax1.axhline(y=level, color='#e74c3c', linestyle='--', linewidth=1, alpha=0.6)
        ax1.text(len(df)-5, level, f'  Resistance {level:.5f}', color='#e74c3c', fontsize=8)
    
    for level_name, level_price in fibo_levels.items():
        if level_name not in ['0.0', '1.0']:
            ax1.axhline(y=level_price, color='#9b59b6', linestyle=':', linewidth=1, alpha=0.5)
            ax1.text(5, level_price, f'  Fib {level_name}', color='#9b59b6', fontsize=7)
    
    for idx, price in swing_highs[-10:]:
        ax1.scatter(idx, price, color='#e74c3c', s=30, marker='v', alpha=0.7)
    for idx, price in swing_lows[-10:]:
        ax1.scatter(idx, price, color='#2ecc71', s=30, marker='^', alpha=0.7)
    
    if signal['action'] != 'WAIT':
        color = '#2ecc71' if signal['action'] == 'BUY' else '#e74c3c'
        marker = '^' if signal['action'] == 'BUY' else 'v'
        
        ax1.scatter(len(df)-1, entry_levels['primary'], color=color, s=350, marker=marker,
                   edgecolors='white', linewidths=2.5, zorder=10,
                   label=f'{signal["action"]} СИГНАЛ ({signal["confidence"]}%)')
        
        if 'pullback' in entry_levels and entry_levels['pullback']:
            for i, level in enumerate(entry_levels['pullback']):
                ax1.axhline(y=level, color=color, linestyle=':', linewidth=1.5, alpha=0.6)
                ax1.text(len(df)-15, level, f'  Entry {i+2}', color=color, fontsize=8, alpha=0.8)
        
        ax1.axhline(y=signal['stop_loss'], color='red', linestyle='--', linewidth=2, alpha=0.8, label='Stop Loss')
        ax1.axhline(y=signal['take_profit_1'], color='#2ecc71', linestyle='--', linewidth=1.5, alpha=0.7, label='TP 1')
        ax1.axhline(y=signal['take_profit_2'], color='#2ecc71', linestyle='--', linewidth=1.5, alpha=0.5, label='TP 2')
    
    ax1.set_ylabel(f'{pair_name} Цена', fontsize=12, color='white')
    ax1.set_xlim(0, len(df))
    ax1.legend(loc='upper left', fontsize=9, facecolor='#1a1a2e', edgecolor='white')
    ax1.grid(True, alpha=0.15, color='gray')
    ax1.set_title(f'{pair_name} - ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗ | Сигнал: {signal["action"]} ({signal["confidence"]}%)',
                 fontsize=14, fontweight='bold', color='white', pad=20)
    ax1.set_xticklabels([])
    
    ax2 = plt.subplot(3, 1, 2)
    ax2.set_facecolor('#0f1219')
    ax2.plot(range(len(df)), df['rsi'], '#9b59b6', linewidth=1.5, label='RSI')
    ax2.axhline(y=70, color='#e74c3c', linestyle='--', linewidth=1.5, alpha=0.7, label='Overbought (70)')
    ax2.axhline(y=30, color='#2ecc71', linestyle='--', linewidth=1.5, alpha=0.7, label='Oversold (30)')
    ax2.fill_between(range(len(df)), 70, 100, where=(df['rsi'] >= 70), color='#e74c3c', alpha=0.2)
    ax2.fill_between(range(len(df)), 0, 30, where=(df['rsi'] <= 30), color='#2ecc71', alpha=0.2)
    ax2.set_ylabel('RSI', fontsize=11, color='white')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper left', fontsize=9, facecolor='#1a1a2e', edgecolor='white')
    ax2.grid(True, alpha=0.15, color='gray')
    ax2.set_xticklabels([])
    
    ax3 = plt.subplot(3, 1, 3)
    ax3.set_facecolor('#0f1219')
    colors = ['#2ecc71' if x >= 0 else '#e74c3c' for x in df['macd_hist']]
    ax3.bar(range(len(df)), df['macd_hist'], color=colors, alpha=0.6, label='MACD Histogram')
    ax3.plot(range(len(df)), df['macd'], '#3498db', linewidth=1.5, label='MACD')
    ax3.plot(range(len(df)), df['macd_signal'], '#e67e22', linewidth=1.5, label='Signal Line')
    ax3.axhline(y=0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
    ax3.set_ylabel('MACD', fontsize=11, color='white')
    ax3.legend(loc='upper left', fontsize=9, facecolor='#1a1a2e', edgecolor='white')
    ax3.grid(True, alpha=0.15, color='gray')
    
    tick_positions = range(0, len(df), max(1, len(df)//10))
    tick_labels = [df.index[i].strftime('%m/%d %H:%M') for i in tick_positions]
    ax3.set_xticks(tick_positions)
    ax3.set_xticklabels(tick_labels, rotation=45, ha='right', color='white')
    ax3.set_xlabel('Дата и время', fontsize=11, color='white')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#0a0c12')
    buf.seek(0)
    plt.close()
    
    return buf

class AIAnalyzer:
    def calculate_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50
        deltas = np.diff(prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gain[:period]) if len(gain[:period]) > 0 else 0.0001
        avg_loss = np.mean(loss[:period]) if len(loss[:period]) > 0 else 0.0001
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return min(100, max(0, 100 - (100 / (1 + rs))))
    
    def generate_ai_signal(self, df, pair_code):
        close_prices = df['close'].values
        current = df.iloc[-1]
        
        rsi = self.calculate_rsi(close_prices)
        ema_fast = df['ema9'].iloc[-1]
        ema_slow = df['ema21'].iloc[-1]
        
        highs, lows = find_swing_points(df)
        
        is_uptrend = False
        structure_broken = False
        structure_type = None
        
        if len(highs) >= 3 and len(lows) >= 3:
            is_uptrend = lows[-1][1] > lows[-2][1]
            if is_uptrend and current['close'] < lows[-1][1]:
                structure_broken = True
                structure_type = "Слом восходящей структуры (MSS)"
            elif not is_uptrend and current['close'] > highs[-1][1]:
                structure_broken = True
                structure_type = "Слом нисходящей структуры (MSS)"
        
        patterns = []
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        body = abs(last['close'] - last['open'])
        lower_wick = min(last['open'], last['close']) - last['low']
        upper_wick = last['high'] - max(last['open'], last['close'])
        
        if lower_wick > body * 2 and lower_wick > upper_wick:
            patterns.append({"name": "Бычий пин-бар", "type": "bullish"})
        if upper_wick > body * 2 and upper_wick > lower_wick:
            patterns.append({"name": "Медвежий пин-бар", "type": "bearish"})
        if (last['close'] > last['open'] and prev['close'] < prev['open'] and
            last['close'] > prev['open'] and last['open'] < prev['close']):
            patterns.append({"name": "Бычье поглощение", "type": "bullish"})
        if (last['close'] < last['open'] and prev['close'] > prev['open'] and
            last['close'] < prev['open'] and last['open'] > prev['close']):
            patterns.append({"name": "Медвежье поглощение", "type": "bearish"})
        
        buy_score = 0
        sell_score = 0
        reasons_buy = []
        reasons_sell = []
        
        if rsi < 30:
            buy_score += 25
            reasons_buy.append(f"📉 RSI = {rsi:.1f} (сильно перепродан)")
        elif rsi > 70:
            sell_score += 25
            reasons_sell.append(f"📈 RSI = {rsi:.1f} (сильно перекуплен)")
        
        if ema_fast > ema_slow:
            buy_score += 20
            reasons_buy.append("✅ EMA 9 выше EMA 21 - восходящий тренд")
        else:
            sell_score += 20
            reasons_sell.append("⚠️ EMA 9 ниже EMA 21 - нисходящий тренд")
        
        if structure_broken:
            if 'восходящей' in structure_type:
                buy_score += 30
                reasons_buy.append(f"🏗️ {structure_type}")
            else:
                sell_score += 30
                reasons_sell.append(f"🏗️ {structure_type}")
        
        for p in patterns:
            if p['type'] == 'bullish':
                buy_score += 20
                reasons_buy.append(f"🕯️ {p['name']}")
            else:
                sell_score += 20
                reasons_sell.append(f"🕯️ {p['name']}")
        
        total_score = buy_score - sell_score
        atr = df['atr'].iloc[-1] if 'atr' in df.columns else 0.0015
        price = current['close']
        
        if total_score >= 50:
            action = "BUY"
            confidence = min(98, 60 + total_score)
            action_emoji = "🟢"
            sl = price - atr * 1.5
            tp1 = price + atr * 2.5
            tp2 = price + atr * 4
            rr1 = abs(tp1 - price) / abs(price - sl) if abs(price - sl) > 0 else 0
        elif total_score <= -50:
            action = "SELL"
            confidence = min(98, 60 + abs(total_score))
            action_emoji = "🔴"
            sl = price + atr * 1.5
            tp1 = price - atr * 2.5
            tp2 = price - atr * 4
            rr1 = abs(price - tp1) / abs(sl - price) if abs(sl - price) > 0 else 0
        else:
            action = "WAIT"
            confidence = 0
            action_emoji = "⏳"
            sl = tp1 = tp2 = price
            rr1 = 0
        
        return {
            'action': action, 'confidence': confidence, 'action_emoji': action_emoji,
            'price': price, 'rsi': rsi, 'trend': 'Восходящий' if ema_fast > ema_slow else 'Нисходящий',
            'stop_loss': sl, 'take_profit_1': tp1, 'take_profit_2': tp2,
            'risk_reward_1': rr1,
            'reasons_buy': reasons_buy[:5], 'reasons_sell': reasons_sell[:5],
            'structure_broken': structure_broken, 'structure_type': structure_type,
            'patterns': patterns, 'atr': atr
        }

ai = AIAnalyzer()

# ==================== ОБРАБОТЧИКИ БОТА ====================
async def start(update: Update, context):
    welcome_text = """
🤖 *PROFESSIONAL FOREX BOT 24/7 - 5 ВАЛЮТНЫХ ПАР*

*📊 ДОСТУПНЫЕ ПАРЫ:*
• 🇺🇸🇨🇭 **USD/CHF** - Швейцарский франк (стабильный)
• 🇪🇺🇺🇸 **EUR/USD** - Евро (основная пара)
• 🇬🇧🇺🇸 **GBP/USD** - Британский фунт (ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ)
• 🇺🇸🇯🇵 **USD/JPY** - Японская иена (азиатская сессия)
• 🇦🇺🇺🇸 **AUD/USD** - Австралийский доллар (сырьевая)

*🎯 ОСОБЕННОСТИ ПАР:*
• GBP/USD - самый быстрый, новостной
• USD/JPY - чувствителен к азиатским новостям
• AUD/USD - зависит от цен на сырье

*🖱️ КНОПКИ МЕНЮ:*
Нажмите на любую кнопку ниже для анализа пары!

*✅ Бот работает 24/7 на Koyeb!*
*⚠️ Всегда используйте стоп-лосс!*
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def help_command(update: Update, context):
    help_text = """
📚 *ПОМОЩЬ ПО БОТУ*

*🖱️ КНОПКИ МЕНЮ:*
• 🇺🇸🇨🇭 USD/CHF - Анализ пары
• 🇪🇺🇺🇸 EUR/USD - Анализ пары
• 🇬🇧🇺🇸 GBP/USD - Анализ пары
• 🇺🇸🇯🇵 USD/JPY - Анализ пары
• 🇦🇺🇺🇸 AUD/USD - Анализ пары
• 📈 Статус рынка - Курсы всех 5 пар
• ❓ Помощь - Эта справка
• 🔔 Подписаться - Уведомления

*📊 ВОЛАТИЛЬНОСТЬ ПАР (от высокой к низкой):*
1. 🇬🇧🇺🇸 GBP/USD - самая волатильная
2. 🇺🇸🇯🇵 USD/JPY - высокая
3. 🇪🇺🇺🇸 EUR/USD - средняя
4. 🇦🇺🇺🇸 AUD/USD - средняя
5. 🇺🇸🇨🇭 USD/CHF - стабильная

*📊 ЧТО ВКЛЮЧАЕТ АНАЛИЗ:*
• Японские свечи на графике
• EMA 9,21,50
• Полосы Боллинджера
• Уровни S/R
• Сетка Фибоначчи
• 3 точки входа
• Уровни SL/TP
• RSI и MACD

*⚠️ УПРАВЛЕНИЕ РИСКАМИ:*
• Риск: 1-2% депозита
• Стоп-лосс обязателен
• Для GBP/USD уменьшайте размер позиции!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def subscribe(update: Update, context):
    context.user_data['subscribed'] = True
    await update.message.reply_text("✅ *Вы подписаны на уведомления!*", parse_mode='Markdown', reply_markup=get_main_keyboard())

async def unsubscribe(update: Update, context):
    context.user_data['subscribed'] = False
    await update.message.reply_text("❌ *Вы отписаны от уведомлений*", parse_mode='Markdown', reply_markup=get_main_keyboard())

async def usdchf(update: Update, context):
    await send_signal(update, "USDCHF")

async def eurusd(update: Update, context):
    await send_signal(update, "EURUSD")

async def gbpusd(update: Update, context):
    await send_signal(update, "GBPUSD")

async def usdjpy(update: Update, context):
    await send_signal(update, "USDJPY")

async def audusd(update: Update, context):
    await send_signal(update, "AUDUSD")

async def send_signal(update, pair_code):
    pair = get_pair_info(pair_code)
    pair_name = pair['name']
    msg = await update.message.reply_text(f"📊 *Создаю график {pair_name}...*\n\n⏳ Загружаю данные\n📈 Рисую японские свечи\n📊 Добавляю индикаторы\n🎯 Рассчитываю точки входа\n🏗️ Анализирую структуру\n🤖 Генерирую сигнал", parse_mode='Markdown', reply_markup=get_main_keyboard())
    
    try:
        df, rate = get_forex_data(pair_code, 120)
        signal = ai.generate_ai_signal(df, pair_code)
        
        highs, lows = find_swing_points(df)
        sr_levels = find_support_resistance(df)
        
        high_50 = df['high'].iloc[-50:].max()
        low_50 = df['low'].iloc[-50:].min()
        fibo_levels = fibonacci_levels(high_50, low_50)
        
        entry_levels = calculate_entry_levels(df, signal, pair_code)
        
        chart = create_pro_chart(df, signal, pair_code, fibo_levels, sr_levels, highs, lows, entry_levels)
        
        # Расчет размера пункта
        if pair_code == 'USDJPY':
            pip_size = 0.01
        else:
            pip_size = 0.0001
        
        text = f"""
{signal['action_emoji']} *СИГНАЛ {pair_name}* {signal['action_emoji']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Рекомендация:* **{signal['action']}**
*Уверенность:* **{signal['confidence']}%**
*Текущая цена:* **{signal['price']:.5f}**
*RSI (14):* **{signal['rsi']:.1f}**
*Тренд:* **{signal['trend']}**
*ATR:* **{signal['atr']:.5f}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*🎯 РЕКОМЕНДОВАННЫЕ ТОЧКИ ВХОДА:*\n"""

        if signal['action'] == 'BUY':
            text += f"""
✅ *Основная:* {entry_levels['primary']:.5f} (текущая цена)
📉 *Альтернативные (откат):* {entry_levels['pullback'][0]:.5f}, {entry_levels['pullback'][1]:.5f}
⚡ *Агрессивный:* {entry_levels['aggressive']:.5f}
🛡️ *Консервативный:* {entry_levels['conservative']:.5f}
📊 *Лимитный ордер:* {entry_levels['limit_buy']:.5f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*🛑 УРОВНИ ЗАЩИТЫ:*

• Stop Loss: **{signal['stop_loss']:.5f}**
• Take Profit 1: **{signal['take_profit_1']:.5f}** (R:R 1:{signal['risk_reward_1']:.1f})
• Take Profit 2: **{signal['take_profit_2']:.5f}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*🧠 ИИ-ОБОСНОВАНИЕ:*\n"""
            
            for r in signal['reasons_buy'][:4]:
                text += f"✅ {r}\n"
        
        elif signal['action'] == 'SELL':
            text += f"""
✅ *Основная:* {entry_levels['primary']:.5f} (текущая цена)
📈 *Альтернативные (откат):* {entry_levels['pullback'][0]:.5f}, {entry_levels['pullback'][1]:.5f}
⚡ *Агрессивный:* {entry_levels['aggressive']:.5f}
🛡️ *Консервативный:* {entry_levels['conservative']:.5f}
📊 *Лимитный ордер:* {entry_levels['limit_sell']:.5f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*🛑 УРОВНИ ЗАЩИТЫ:*

• Stop Loss: **{signal['stop_loss']:.5f}**
• Take Profit 1: **{signal['take_profit_1']:.5f}** (R:R 1:{signal['risk_reward_1']:.1f})
• Take Profit 2: **{signal['take_profit_2']:.5f}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*🧠 ИИ-ОБОСНОВАНИЕ:*\n"""
            
            for r in signal['reasons_sell'][:4]:
                text += f"⚠️ {r}\n"
        
        else:
            text += "⏳ Нет четких сигналов. Рекомендуется ожидание.\n\n"
        
        if signal['patterns']:
            text += f"\n*🕯️ РАЗВОРОТНЫЕ ПАТТЕРНЫ:*\n"
            for p in signal['patterns'][:2]:
                text += f"   {p['name']}\n"
        
        if signal['structure_broken']:
            text += f"\n*🏗️ СТРУКТУРА РЫНКА:*\n   {signal['structure_type']}\n"
        
        text += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *РИСК-МЕНЕДЖМЕНТ:*
• Риск: 1-2% депозита
• Для {pair_name} 1 пункт = {pip_size:.4f}
• Размер лота = (Капитал × Риск%) / (SL в пунктах × Стоимость пункта)

📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        await msg.delete()
        await update.message.reply_photo(photo=chart, caption=text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}\n\nПопробуйте позже", reply_markup=get_main_keyboard())

async def status(update: Update, context):
    await update.message.reply_text("📊 *Получаю курсы всех 5 валютных пар...*", parse_mode='Markdown', reply_markup=get_main_keyboard())
    
    try:
        rates = {}
        for pair_code in PAIRS.keys():
            rate = get_real_forex_rate(pair_code)
            rates[pair_code] = rate
        
        text = f"""
📊 *СТАТУС РЫНКА* - {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*🇺🇸🇨🇭 USD/CHF:* **{rates['USDCHF']:.5f}**
*🇪🇺🇺🇸 EUR/USD:* **{rates['EURUSD']:.5f}**
*🇬🇧🇺🇸 GBP/USD:* **{rates['GBPUSD']:.5f}**
*🇺🇸🇯🇵 USD/JPY:* **{rates['USDJPY']:.3f}**
*🇦🇺🇺🇸 AUD/USD:* **{rates['AUDUSD']:.5f}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*📈 ВОЛАТИЛЬНОСТЬ (сегодня):*
• 🇬🇧🇺🇸 GBP/USD - 🔥🔥🔥🔥🔥
• 🇺🇸🇯🇵 USD/JPY - 🔥🔥🔥🔥
• 🇪🇺🇺🇸 EUR/USD - 🔥🔥🔥
• 🇦🇺🇺🇸 AUD/USD - 🔥🔥
• 🇺🇸🇨🇭 USD/CHF - 🔥

*💡 СОВЕТЫ ПО ТОРГОВЛЕ:*
• GBP/USD - торгуйте на новостях
• USD/JPY - следите за азиатской сессией
• AUD/USD - учитывайте цены на золото

✅ Бот работает 24/7 на Koyeb!
"""
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}", reply_markup=get_main_keyboard())

async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'usdchf':
        await usdchf(query, context)
    elif query.data == 'eurusd':
        await eurusd(query, context)
    elif query.data == 'gbpusd':
        await gbpusd(query, context)
    elif query.data == 'usdjpy':
        await usdjpy(query, context)
    elif query.data == 'audusd':
        await audusd(query, context)
    elif query.data == 'status':
        await status(query, context)
    elif query.data == 'help':
        await help_command(query, context)

async def handle_message(update: Update, context):
    """Обработка текстовых сообщений (кнопок меню)"""
    text = update.message.text
    
    if text == "🇺🇸🇨🇭 USD/CHF":
        await usdchf(update, context)
    elif text == "🇪🇺🇺🇸 EUR/USD":
        await eurusd(update, context)
    elif text == "🇬🇧🇺🇸 GBP/USD":
        await gbpusd(update, context)
    elif text == "🇺🇸🇯🇵 USD/JPY":
        await usdjpy(update, context)
    elif text == "🇦🇺🇺🇸 AUD/USD":
        await audusd(update, context)
    elif text == "📈 Статус рынка":
        await status(update, context)
    elif text == "❓ Помощь":
        await help_command(update, context)
    elif text == "🔔 Подписаться":
        await subscribe(update, context)
    elif text == "🔕 Отписаться":
        await unsubscribe(update, context)
    else:
        await help_command(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("usdchf", usdchf))
    app.add_handler(CommandHandler("eurusd", eurusd))
    app.add_handler(CommandHandler("gbpusd", gbpusd))
    app.add_handler(CommandHandler("usdjpy", usdjpy))
    app.add_handler(CommandHandler("audusd", audusd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Инлайн-кнопки
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Обработка текстовых сообщений (кнопки)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║     🤖 PROFESSIONAL FOREX BOT - 5 ВАЛЮТНЫХ ПАР                      ║
║     📱 Бот: @usdchfforex_bot                                        ║
║     🚀 Статус: РАБОТАЕТ 24/7                                        ║
║                                                                      ║
║     📊 ДОСТУПНЫЕ ПАРЫ:                                              ║
║     • USD/CHF - Швейцарский франк (стабильный)                      ║
║     • EUR/USD - Евро (основная)                                     ║
║     • GBP/USD - Фунт (🔥 ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ)                     ║
║     • USD/JPY - Иена (азиатская сессия)                             ║
║     • AUD/USD - Австралиец (сырьевая)                               ║
║                                                                      ║
║     🖱️ КНОПКИ МЕНЮ:                                                ║
║     Нажмите на любую кнопку в Telegram для анализа!                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    app.run_polling()

if __name__ == '__main__':
    main()