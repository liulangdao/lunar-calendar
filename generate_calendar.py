import datetime
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

def generate_ics():
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

        # Description text
        description = "\n".join(desc_lines)

        # Create Event
        event = Event()
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
