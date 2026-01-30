import soccerdata as sd
import pandas as pd
import requests
import datetime
import os
from datetime import timedelta

# ---------------------------------------------------------
# 🔐 보안 설정: 깃허브 금고(Secrets)에서 키를 꺼내옵니다
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

def run_alpha_hunter():
    print("🚀 Alpha Hunter Started...")
    
    # 5대 리그 설정
    leagues = ['ENG-Premier League', 'ESP-La Liga', 'GER-Bundesliga', 'ITA-Serie A', 'FRA-Ligue 1']
    
    # 현재 시즌 데이터 로드 (2025-2026 시즌)
    try:
        fb = sd.FBref(leagues=leagues, seasons='2025')
        schedule = fb.read_schedule()
        
        # ELO 데이터 로드
        elo = sd.ClubElo()
        df_elo = elo.read_by_date().reset_index()
    except Exception as e:
        send_telegram(f"⚠️ 데이터 수집 중 오류 발생: {e}")
        return

    # 날짜 필터링 (오늘 ~ 3일 뒤)
    today = datetime.datetime.now().date()
    end_date = today + timedelta(days=3)
    
    upcoming = schedule[(schedule['date'].dt.date >= today) & (schedule['date'].dt.date <= end_date)]
    
    if upcoming.empty:
        send_telegram("💤 예정된 5대 리그 경기가 없습니다.")
        return

    report = f"🌍 **Alpha Hunter Daily**\n({today} ~ {end_date})\n\n"
    count = 0
    
    for idx, row in upcoming.iterrows():
        home, away = row['home_team'], row['away_team']
        league = idx[0].split('-')[1]
        time = row['date'].strftime("%m/%d %H:%M")
        
        try:
            h_elo = df_elo[df_elo['team'] == home]['elo'].values[0]
            a_elo = df_elo[df_elo['team'] == away]['elo'].values[0]
            
            # 승률 계산
            dr = h_elo + 100 - a_elo
            prob = 1 / (10**(dr/400) + 1)
            prob_pct = (1 - prob) * 100
            
            # 승률 65% 이상만 추천
            if prob_pct >= 65:
                count += 1
                emoji = "🔥" if prob_pct >= 75 else "✅"
                report += f"{emoji} **[{league}]**\n⚽ {home} vs {away}\n🧠 승률: {prob_pct:.1f}%\n\n"
        except:
            continue

    if count > 0:
        if len(report) > 4000: report = report[:4000] + "\n...(생략)"
        send_telegram(report)
    else:
        send_telegram("📉 분석 완료: 추천할 만한 안전한 경기가 없습니다.")

if __name__ == "__main__":
    run_alpha_hunter()
