import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 🔐 텔레그램 설정 (GitHub Secrets에서 가져옴)
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending telegram: {e}")

def run_alpha_hunter():
    print("🚀 Alpha Hunter: ClubElo API 모드로 가동...")
    
    # 1. ClubElo 공식 API에서 '예정된 경기' 데이터(CSV)를 직접 가져옵니다.
    # 이 주소는 차단되지 않으며, 전 세계 주요 경기의 ELO 데이터를 포함합니다.
    url = "https://api.clubelo.com/fixtures"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            send_telegram(f"⚠️ 데이터 접속 실패: 상태 코드 {response.status_code}")
            return
            
        # CSV 데이터를 판다스로 읽기
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        
    except Exception as e:
        send_telegram(f"⚠️ 데이터 처리 중 오류: {e}")
        return

    # 2. 날짜 필터링 (오늘 ~ 3일 뒤)
    # ClubElo 데이터의 'Date' 컬럼은 'YYYY-MM-DD' 형식입니다.
    today = datetime.now().date()
    end_date = today + timedelta(days=3)
    
    # 날짜 형식 변환
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # 기간 내 경기만 남기기
    upcoming = df[(df['Date'] >= today) & (df['Date'] <= end_date)].copy()
    
    # 3. 5대 리그 + 주요 리그만 필터링 (Country 레벨로 필터링)
    # ClubElo는 리그명이 아니라 국가(Country)와 레벨(Level)로 구분합니다.
    # Level 1 = 1부 리그
    major_countries = ['ENG', 'ESP', 'GER', 'ITA', 'FRA'] 
    
    targets = upcoming[
        (upcoming['Country'].isin(major_countries)) & 
        (upcoming['Level'] == 1)
    ]
    
    if targets.empty:
        send_telegram(f"💤 {today}~{end_date} 기간에 예정된 5대 리그 경기가 없습니다.")
        return

    report = f"🌍 **Alpha Hunter Global**\n(Source: ClubElo Official)\n\n"
    count = 0
    
    # 4. 분석 및 리포트 작성
    for idx, row in targets.iterrows():
        home = row['Home']
        away = row['Away']
        h_elo = row['HomeElo']
        a_elo = row['AwayElo']
        country = row['Country']
        date_str = row['Date'].strftime("%m/%d")
        
        # 승률 계산 (ELO 공식)
        dr = h_elo + 100 - a_elo # 홈 어드밴티지 +100
        win_prob = 1 / (10**(dr/400) + 1)
        prob_pct = (1 - win_prob) * 100
        
        # 승률 60% 이상이거나 빅매치인 경우 추천
        if prob_pct >= 60:
            count += 1
            emoji = "🔥" if prob_pct >= 70 else "✅"
            
            report += f"{emoji} **[{country} 1부]** {date_str}\n"
            report += f"⚽ **{home}** vs {away}\n"
            report += f"🧠 승률: **{prob_pct:.1f}%** (ELO차: {int(h_elo - a_elo)})\n"
            report += "------------------\n"

    # 메시지 전송
    if count > 0:
        if len(report) > 4000: report = report[:4000] + "\n...(생략)"
        send_telegram(report)
        print("✅ 텔레그램 전송 완료")
    else:
        send_telegram(f"📉 분석 완료: {today} 기준 추천할 만한 경기가 없습니다.")

if __name__ == "__main__":
    run_alpha_hunter()
