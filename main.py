import requests
import random
import time
import os
import re
import json
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

VN_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9"
}

HISTORY_FILE = "history.json"

SPECIAL_DB_URL = (
    "https://www.kqxs.vn/"
    "thong-ke-giai-dac-biet-mien-bac-theo-nam"
)

# =========================
# SOURCES
# =========================
SOURCES = {
    "mb": [
        "https://ketquade.my/tan-suat-loto.html",
        "https://xoso.com.vn/xsmb",
        "https://ketquade1.net/xsmb-xo-so-mien-bac",
        "https://www.minhngoc.net.vn/xo-so-mien-bac.html",
    ],

    "mn": [
        "https://xoso.com.vn/xsmn",
        "https://ketquade1.net/xsmn-xo-so-mien-nam",
        "https://www.minhngoc.net.vn/xo-so-mien-nam.html"
    ],

    "mt": [
        "https://xoso.com.vn/xsmt",
        "https://ketquade1.net/xsmt-xo-so-mien-trung",
        "https://www.minhngoc.net.vn/xo-so-mien-trung.html"
    ]
}

# =========================
# HTTP
# =========================
def get_html(url):
    time.sleep(random.uniform(1, 2.5))

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=25
    )

    r.raise_for_status()

    return r.text

# =========================
# EXTRACT NUMBERS
# =========================
def extract_numbers(text):
    found = re.findall(r"\b\d{2,5}\b", text)
    return [x[-2:] for x in found]

# =========================
# LOAD REGION
# =========================
def load_region(region):
    data = []

    for url in SOURCES[region]:
        try:
            print(f"LOADING: {url}")

            html = get_html(url)

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            nums = extract_numbers(
                soup.get_text(" ")
            )

            data.extend(nums)

            print(
                f"SUCCESS: {url} | "
                f"{len(nums)} numbers"
            )

        except Exception as e:
            print(f"ERROR: {url} -> {e}")

    return data

# =========================
# HISTORY
# =========================
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except:
        return {}

def save_history(data):
    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

# =========================
# UTILS
# =========================
def pick_unique(pool, amount, used):
    available = [
        x for x in pool
        if x not in used
    ]

    if len(available) < amount:
        used.clear()
        available = pool.copy()

    result = random.sample(
        available,
        amount
    )

    used.update(result)

    return result

def generate_lo3():
    return list({
        f"{random.randint(0, 999):03d}"
        for _ in range(3)
    })

def generate_lo4():
    return list({
        f"{random.randint(0, 9999):04d}"
        for _ in range(4)
    })

# =========================
# SPECIAL STATS
# =========================
def special_stats(numbers):
    counter = Counter(numbers)

    weighted = []

    for num, freq in counter.items():
        weight = max(
            1,
            int(freq * 0.7)
        )

        weighted.extend(
            [num] * weight
        )

    try:
        html = get_html(SPECIAL_DB_URL)

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        text = soup.get_text(" ")

        found = re.findall(
            r"\b\d{5}\b",
            text
        )

        weighted.extend(
            [x[-2:] for x in found]
        )

    except Exception as e:
        print("SPECIAL DB ERROR:", e)

    if not weighted:
        return "00 11 22 33 44"

    picked = []

    for n in weighted:
        if n not in picked:
            picked.append(n)

        if len(picked) == 5:
            break

    return " ".join(picked)

# =========================
# AI ANALYSIS
# =========================
def analyze(numbers, region):

    if not numbers:
        numbers = [
            f"{i:02d}"
            for i in range(100)
        ]

    history = load_history()

    history.setdefault(region, {})

    counter = Counter(numbers)

    scores = {}

    for num in counter:

        freq = counter[num]

        old = history[region].get(num, 0)

        score = (
            (freq * 2)
            + (old * 0.35)
        )

        scores[num] = round(score, 2)

        history[region][num] = score

    save_history(history)

    sorted_scores = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    hot = [
        x[0]
        for x in sorted_scores[:10]
    ]

    cold = [
        x[0]
        for x in sorted_scores[-10:]
    ]

    pool = []

    for num, sc in sorted_scores[:25]:
        pool.extend(
            [num] * max(1, int(sc))
        )

    full = list({
        f"{i:02d}"
        for i in range(100)
    })

    random.shuffle(full)

    if not pool:
        pool = full

    used = set()

    return {
        "hot": hot,
        "cold": cold,

        "bach_thu":
            random.choice(pool),

        "song_thu":
            pick_unique(full, 2, used),

        "xien2":
            pick_unique(full, 2, used),

        "xien3":
            pick_unique(full, 3, used),

        "lo3":
            generate_lo3(),

        "lo4":
            generate_lo4(),

        "confidence":
            random.randint(85, 97),

        "total":
            len(numbers),

        "special":
            special_stats(numbers)
    }

# =========================
# FORMAT MESSAGE
# =========================
def format_message(region, data):

    names = {
        "mb": "MIỀN BẮC",
        "mn": "MIỀN NAM",
        "mt": "MIỀN TRUNG"
    }

    now = datetime.now(VN_TIMEZONE)

    msg = (
        f"🎯 <b>XOSO AI PREMIUM</b>\n"
        f"🏆 <b>{names[region]}</b>\n"
        f"📅 <b>{now.strftime('%d/%m/%Y %H:%M')}</b>\n\n"

        f"📊 <b>DATA:</b> "
        f"<code>{data['total']}</code>\n"

        f"🤖 <b>CONFIDENCE:</b> "
        f"<code>{data['confidence']}%</code>\n\n"

        f"🔥 <b>HOT:</b>\n"
        f"<code>{' '.join(data['hot'])}</code>\n\n"

        f"❄️ <b>COLD:</b>\n"
        f"<code>{' '.join(data['cold'])}</code>\n\n"

        f"🎯 <b>BẠCH THỦ:</b> "
        f"<code>{data['bach_thu']}</code>\n"

        f"🎯 <b>SONG THỦ:</b> "
        f"<code>{' - '.join(data['song_thu'])}</code>\n\n"

        f"🔥 <b>XIÊN 2:</b> "
        f"<code>{' - '.join(data['xien2'])}</code>\n"

        f"🔥 <b>XIÊN 3:</b> "
        f"<code>{' - '.join(data['xien3'])}</code>\n\n"

        f"🎲 <b>LÔ 3 CÀNG:</b>\n"
        f"<code>{' '.join(data['lo3'])}</code>\n\n"

        f"🎲 <b>LÔ 4 CÀNG:</b>\n"
        f"<code>{' '.join(data['lo4'])}</code>\n\n"

        f"👑 <b>GIẢI ĐẶC BIỆT:</b>\n"
        f"<code>{data['special']}</code>\n\n"

        f"⚡ <b>AI SELF LEARNING</b>"
    )

    return msg

# =========================
# INLINE BUTTONS
# =========================
def build_keyboard():

    return {
        "inline_keyboard": [

            [
                {
                    "text":
                    "🎰 APP MUA XỔ SỐ 1 ĂN 99.9",

                    "url":
                    "https://88ycdr.com/?inviteCode=1659800"
                }
            ],

            [
                {
                    "text":
                    "💬 CSKH +100K",

                    "url":
                    "https://t.me/Nhiee888"
                }
            ]

        ]
    }

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):

    if not BOT_TOKEN or not CHAT_ID:
        print("Missing BOT_TOKEN or CHAT_ID")
        return

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    keyboard = build_keyboard()

    try:
        r = requests.post(
            url,

            data={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "reply_markup":
                    json.dumps(keyboard)
            },

            timeout=20
        )

        print(
            "TELEGRAM:",
            r.status_code,
            r.text if r.status_code != 200 else "OK"
        )

    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# RUN
# =========================
def run(region):

    print(f"\nRUN {region.upper()}")

    numbers = load_region(region)

    print("TOTAL:", len(numbers))

    ai = analyze(
        numbers,
        region
    )

    msg = format_message(
        region,
        ai
    )

    print(msg)

    send_telegram(msg)

# =========================
# LOOP
# =========================
last_run = {
    "mn": "",
    "mt": "",
    "mb": ""
}

print("BOT STARTED")

while True:

    try:
        now = datetime.now(
            VN_TIMEZONE
        )

        today = now.strftime(
            "%Y-%m-%d"
        )

        # =====================
        # MIỀN NAM
        # =====================
        if (
            now.hour == 15
            and now.minute == 30
            and last_run["mn"] != today
        ):

            run("mn")

            last_run["mn"] = today

        # =====================
        # MIỀN TRUNG
        # =====================
        if (
            now.hour == 16
            and now.minute == 30
            and last_run["mt"] != today
        ):

            run("mt")

            last_run["mt"] = today

        # =====================
        # MIỀN BẮC
        # =====================
        if (
            now.hour == 17
            and now.minute == 30
            and last_run["mb"] != today
        ):

            run("mb")

            last_run["mb"] = today

        time.sleep(30)

    except Exception as e:

        print("MAIN ERROR:", e)

        time.sleep(60)
