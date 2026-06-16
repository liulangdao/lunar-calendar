import datetime
import json
import urllib.request
from datetime import date, timedelta
from lunar_python import Solar, Lunar
from icalendar import Calendar, Event

XIU_DICT = {
    "角": "角木蛟 (吉)",
    "亢": "亢金龙 (凶)",
    "氐": "氐土貉 (凶)",
    "房": "房日兔 (吉)",
    "心": "心月狐 (凶)",
    "尾": "尾火虎 (吉)",
    "箕": "箕水豹 (吉)",
    "斗": "斗木獬 (吉)",
    "牛": "牛金牛 (凶)",
    "女": "女土蝠 (凶)",
    "虚": "虚日鼠 (凶)",
    "危": "危月燕 (凶)",
    "室": "室火猪 (吉)",
    "壁": "壁水狳 (吉)",
    "奎": "奎木狼 (凶)",
    "娄": "娄金狗 (吉)",
    "胃": "胃土雉 (吉)",
    "昴": "昴日鸡 (凶)",
    "毕": "毕月乌 (吉)",
    "觜": "觜火猴 (凶)",
    "参": "参水猿 (吉)",
    "井": "井木犴 (吉)",
    "鬼": "鬼金羊 (凶)",
    "柳": "柳土獐 (凶)",
    "星": "星日马 (凶)",
    "张": "张月鹿 (吉)",
    "翼": "翼火蛇 (凶)",
    "轸": "轸水蚓 (吉)"
}

PROMOTED_FESTIVALS = {
    "万圣节",
    "平安夜",
    "白色情人节",
    "世界地球日",
    "世界环境日",
    "世界睡眠日",
    "世界读书日",
    "世界水日",
    "世界无烟日",
    "世界红十字日",
    "世界艾滋病日",
    "世界粮食日",
    "世界人口日",
    "世界青年节",
    "世界儿童日",
    "世界残疾人日",
    "程序员节",
    "光棍节",
    "女生节",
}

# WMO weather code -> Chinese description (used by Open-Meteo)
WEATHER_CODE_ZH = {
    0: "晴",
    1: "基本晴", 2: "局部多云", 3: "阴",
    45: "雾", 48: "冻雾",
    51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
    56: "轻冻毛毛雨", 57: "重冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "轻冻雨", 67: "重冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "小阵雨", 81: "中阵雨", 82: "强阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷暴", 96: "雷暴伴小冰雹", 99: "雷暴伴大冰雹",
}


def _deg_to_zh(deg):
    """Convert wind direction in degrees to Chinese compass label."""
    dirs = ["北", "北偏东", "东北", "东偏北",
            "东", "东偏南", "东南", "南偏东",
            "南", "南偏西", "西南", "西偏南",
            "西", "西偏北", "西北", "北偏西"]
    idx = round(deg / 22.5) % 16
    return dirs[idx]


def fetch_lishui_weather():
    """Fetch 16-day weather forecast for Lishui from Open-Meteo (free, no API key).
    Returns a dict mapping date string (YYYY-MM-DD) to weather info, or empty dict on failure.
    Lishui, Zhejiang: 28.4568°N, 119.9228°E
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=28.4568&longitude=119.9228"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        ",weathercode,windspeed_10m_max,winddirection_10m_dominant"
        "&timezone=Asia%2FShanghai&forecast_days=16"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        daily = data["daily"]
        weather_map = {}
        for i, day_date in enumerate(daily["time"]):
            code = int(daily["weathercode"][i] or 0)
            desc_zh = WEATHER_CODE_ZH.get(code, f"代码{code}")
            min_c = round(daily["temperature_2m_min"][i] or 0)
            max_c = round(daily["temperature_2m_max"][i] or 0)
            rain_chance = int(daily["precipitation_probability_max"][i] or 0)
            wind_speed = round(daily["windspeed_10m_max"][i] or 0)
            wind_deg = daily["winddirection_10m_dominant"][i] or 0
            wind_dir = _deg_to_zh(wind_deg)
            weather_map[day_date] = {
                "desc": desc_zh,
                "min_c": min_c,
                "max_c": max_c,
                "rain_chance": rain_chance,
                "wind_speed": wind_speed,
                "wind_dir": wind_dir,
            }
        return weather_map
    except Exception as e:
        print(f"[天气] 获取丽水天气失败: {e}")
        return {}


def generate_ics():
    # Fetch Lishui weather forecast (covers today + next 2 days)
    print("[天气] 正在从 Open-Meteo 获取丽水16天天气预报...")
    weather_map = fetch_lishui_weather()
    if weather_map:
        print(f"[天气] 成功获取 {len(weather_map)} 天预报: {', '.join(sorted(weather_map.keys()))}")
    else:
        print("[天气] 未能获取天气数据，将跳过天气信息。")

    # Define range: previous, current, next year
    current_year = datetime.datetime.now().year
    start_date = date(current_year - 1, 1, 1)
    end_date = date(current_year + 1, 12, 31)

    cal = Calendar()
    cal.add('prodid', '-//Traditional Chinese Lunar Calendar and Huangli//CN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', '农历黄历订阅')
    cal.add('x-wr-timezone', 'Asia/Shanghai')
    cal.add('x-wr-caldesc', '包含农历、干支、节日、节气、每日宜忌与深度老黄历信息')

    delta = end_date - start_date
    for i in range(delta.days + 1):
        cur_date = start_date + timedelta(days=i)
        solar = Solar.fromYmd(cur_date.year, cur_date.month, cur_date.day)
        lunar = solar.getLunar()

        # Festivals & Solar Term
        jieqi = lunar.getJieQi()
        main_festivals = lunar.getFestivals() + solar.getFestivals()
        
        # Promote key international/other festivals to the title
        promoted = []
        for f in lunar.getOtherFestivals() + solar.getOtherFestivals():
            if f in PROMOTED_FESTIVALS and f not in main_festivals:
                promoted.append(f)
        
        # Title
        lunar_date_str = f"农历{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"
        title_parts = [lunar_date_str]
        if jieqi:
            title_parts.append(jieqi)
        if main_festivals:
            title_parts.extend(main_festivals)
        if promoted:
            title_parts.extend(promoted)
        title = " · ".join(title_parts)

        # Description construction
        desc_lines = []
        
        # 1. Basic Info
        desc_lines.append(f"📅 农历日期：{lunar.getYearInGanZhi()}({lunar.getYearShengXiao()})年 {lunar.getMonthInGanZhi()}({lunar.getMonthShengXiao()})月 {lunar.getDayInGanZhi()}({lunar.getDayShengXiao()})日 ({lunar_date_str})")
        
        # BaZi
        bazi = lunar.getEightChar()
        desc_lines.append(f"☯️ 八字：{bazi.getYear()} {bazi.getMonth()} {bazi.getDay()}")
        
        # WuXing / NaYin
        desc_lines.append(f"🔮 五行纳音：{lunar.getDayNaYin()}")
        desc_lines.append("")

        # 2. Yiji
        yi = lunar.getDayYi() if hasattr(lunar, 'getDayYi') else (lunar.getYi() if hasattr(lunar, 'getYi') else [])
        ji = lunar.getDayJi() if hasattr(lunar, 'getDayJi') else (lunar.getJi() if hasattr(lunar, 'getJi') else [])
        desc_lines.append(f"🟢 宜：{'、'.join(yi) if yi else '无'}")
        desc_lines.append(f"🔴 忌：{'、'.join(ji) if ji else '无'}")
        desc_lines.append("")

        # 3. Festivals & Other Festivals
        all_festivals = []
        for f in lunar.getFestivals() + solar.getFestivals():
            if f not in all_festivals:
                all_festivals.append(f)
        for f in lunar.getOtherFestivals() + solar.getOtherFestivals():
            if f not in all_festivals:
                all_festivals.append(f)
        if all_festivals:
            desc_lines.append(f"🎉 节日：{'、'.join(all_festivals)}")
            
        # Solar Term details if applicable
        if jieqi:
            desc_lines.append(f"🔆 节气：{jieqi}")
        if all_festivals or jieqi:
            desc_lines.append("")

        # 4. Detailed Huangli
        desc_lines.append(f"🐎 冲煞：冲{lunar.getDayChongDesc()}，煞{lunar.getDaySha()}")
        desc_lines.append(f"🚪 胎神占方：{lunar.getDayPositionTai()}")
        
        pz_gan = lunar.getPengZuGan() if hasattr(lunar, 'getPengZuGan') else ""
        pz_zhi = lunar.getPengZuZhi() if hasattr(lunar, 'getPengZuZhi') else ""
        desc_lines.append(f"📌 彭祖百忌：{pz_gan} {pz_zhi}")
        
        desc_lines.append(f"🔱 建除十二神：{lunar.getZhiXing()}日")
        
        # Nine Star
        ns = lunar.getDayNineStar()
        desc_lines.append(f"🌌 九星：{ns.toFullString() if hasattr(ns, 'toFullString') else str(ns)}")
        
        # Constellation
        xiu = lunar.getXiu()
        xiu_luck = lunar.getXiuLuck()
        xiu_desc = XIU_DICT.get(xiu, f"{xiu}宿 ({xiu_luck})")
        desc_lines.append(f"⭐ 二十八宿：{xiu_desc}")
        desc_lines.append(f"📖 宿歌诀：{lunar.getXiuSong()}")
        desc_lines.append("")

        # 5. Deities
        jishen = lunar.getDayJiShen()
        xiongsha = lunar.getDayXiongSha()
        desc_lines.append(f"✨ 吉神宜趋：{'、'.join(jishen) if jishen else '无'}")
        desc_lines.append(f"⚠️ 凶神宜忌：{'、'.join(xiongsha) if xiongsha else '无'}")

        # 6. Lishui Weather (only for days with forecast data)
        date_str_key = cur_date.strftime("%Y-%m-%d")
        if date_str_key in weather_map:
            w = weather_map[date_str_key]
            desc_lines.append("")
            desc_lines.append(f"🌤️ 丽水天气：{w['desc']}  {w['min_c']}~{w['max_c']}°C")
            desc_lines.append(f"🌧️ 降雨概率：{w['rain_chance']}%")
            desc_lines.append(f"💨 风向风速：{w['wind_dir']}风 {w['wind_speed']} km/h")

        # Description text
        description = "\n".join(desc_lines)

        # Create Event
        event = Event()
        # Add weather emoji to title for days with forecast
        date_str_key = cur_date.strftime("%Y-%m-%d")
        if date_str_key in weather_map:
            w = weather_map[date_str_key]
            weather_title = f"☁️{w['min_c']}~{w['max_c']}°C" if "云" in w['desc'] or "阴" in w['desc'] else \
                            f"🌧️{w['min_c']}~{w['max_c']}°C" if any(k in w['desc'] for k in ["雨", "雪", "粒", "冻"]) else \
                            f"⛅{w['min_c']}~{w['max_c']}°C" if "局部" in w['desc'] else \
                            f"☀️{w['min_c']}~{w['max_c']}°C"
            title = title + " | " + weather_title
        event.add('summary', title)
        event.add('description', description)
        event.add('dtstart', cur_date)
        # End date is exclusive in iCalendar for all-day events
        event.add('dtend', cur_date + timedelta(days=1))
        
        # Stable UID: format date + domain
        uid = f"lunar-huangli-{cur_date.strftime('%Y%m%d')}@github.com"
        event.add('uid', uid)
        
        cal.add_component(event)

    # Write to file
    output_path = 'lunar_huangli.ics'
    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())
        
    print(f"Successfully generated {output_path} with {len(cal.walk('VEVENT'))} events.")

if __name__ == "__main__":
    generate_ics()
