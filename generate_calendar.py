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

# Weather code -> Chinese description mapping
WEATHER_CODE_ZH = {
    113: "晴", 116: "局部多云", 119: "多云", 122: "阴",
    143: "薄雾", 176: "局部阵雨", 179: "局部阵雪", 182: "局部冰粒",
    185: "局部冻毛毛雨", 200: "局部雷阵雨", 227: "局部飘雪", 230: "暴雪",
    248: "雾", 260: "冻雾", 263: "轻微毛毛雨", 266: "毛毛雨",
    281: "冻毛毛雨", 284: "大冻毛毛雨", 293: "局部小雨", 296: "小雨",
    299: "时而中雨", 302: "中雨", 305: "时而大雨", 308: "大雨",
    311: "轻冻雨", 314: "中冻雨", 317: "轻冰粒", 320: "中冰粒",
    323: "局部轻雪", 326: "局部小雪", 329: "局部中雪", 332: "中雪",
    335: "局部大雪", 338: "大雪", 350: "冰粒", 353: "小阵雨",
    356: "中到大阵雨", 359: "暴雨", 362: "轻到中阵冰粒", 365: "中到大阵冰粒",
    368: "小阵雪", 371: "中到大阵雪", 374: "轻到中阵冰粒", 377: "中到大阵冰粒",
    386: "局部雷阵雨", 389: "中到大雷暴雨", 392: "局部雷雪", 395: "中到大雷雪",
}

WIND_DIR_ZH = {
    "N": "北", "NNE": "北偏东", "NE": "东北", "ENE": "东偏北",
    "E": "东", "ESE": "东偏南", "SE": "东南", "SSE": "南偏东",
    "S": "南", "SSW": "南偏西", "SW": "西南", "WSW": "西偏南",
    "W": "西", "WNW": "西偏北", "NW": "西北", "NNW": "北偏西",
}


def fetch_lishui_weather():
    """Fetch 3-day weather forecast for Lishui from wttr.in (no API key required).
    Returns a dict mapping date string (YYYY-MM-DD) to weather info, or empty dict on failure.
    """
    url = "https://wttr.in/%E4%B8%BD%E6%B0%B4,Zhejiang?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        weather_map = {}
        for day in data.get("weather", []):
            day_date = day["date"]  # "YYYY-MM-DD"
            min_c = day["mintempC"]
            max_c = day["maxtempC"]
            # Pick midday (time=1200) hourly slot for representative description
            hourly = day.get("hourly", [])
            mid_slot = next((h for h in hourly if h["time"] == "1200"), hourly[4] if len(hourly) > 4 else hourly[0] if hourly else {})
            code = int(mid_slot.get("weatherCode", 113))
            desc_zh = WEATHER_CODE_ZH.get(code, mid_slot.get("weatherDesc", [{}])[0].get("value", ""))
            humidity = mid_slot.get("humidity", "")
            wind_dir = WIND_DIR_ZH.get(mid_slot.get("winddir16Point", ""), mid_slot.get("winddir16Point", ""))
            wind_speed = mid_slot.get("windspeedKmph", "")
            rain_chance = mid_slot.get("chanceofrain", "0")
            weather_map[day_date] = {
                "desc": desc_zh,
                "min_c": min_c,
                "max_c": max_c,
                "humidity": humidity,
                "wind_dir": wind_dir,
                "wind_speed": wind_speed,
                "rain_chance": rain_chance,
            }
        return weather_map
    except Exception as e:
        print(f"[天气] 获取丽水天气失败: {e}")
        return {}


def generate_ics():
    # Fetch Lishui weather forecast (covers today + next 2 days)
    print("[天气] 正在获取丽水天气预报...")
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
            desc_lines.append(f"💧 湿度：{w['humidity']}%　🌧️ 降雨概率：{w['rain_chance']}%")
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
