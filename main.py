import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 🔐 텔레그램 설정
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending telegram: {e}")

def run_alpha_hunter():
    print("🚀 Alpha Hunter: Stealth Mode (위장 접속 시도)...")
    
    # 1. 방화벽 우회를 위한 가짜 신분증(User-Agent) 만들기
    # 마치 크롬 브라우저로 접속하는 척합니다.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    url = "https://api.clubelo.com/fixtures"
    
    try:
        # timeout=30: 30초 동안 응답 없으면 멈춤
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            send_telegram(f"⚠️ 접속 거부됨: 상태 코드 {response.status_code}")
            return
            
        # 데이터 읽기
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        
    except Exception as e:
        send_telegram(f"⚠️ 데이터 접속 실패 (방화벽): {e}")
        return

    # 2. 날짜 필터링 (오늘 ~ 3일 뒤)
    today = datetime.now().date()
    end_date = today + timedelta(days=3)
    
    # 날짜 형식 변환
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # 3. 주요 리그 필터링 (ENG, ESP, GER, ITA, FRA)
    major_countries = ['ENG', 'ESP', 'GER', 'ITA', 'FRA'] 
    
    # 기간 내 + 1부 리그 + 주요 국가
    upcoming = df[
        (df['Date'] >= today) & 
        (df['Date'] <= end_date) &
        (df['Country'].isin(major_countries)) &
        (df['Level'] == 1)
    ].copy()
    
    if upcoming.empty:
        send_telegram(f"💤 {today}~{end_date} 기간에 예정된 주요 경기가 없습니다.")
        return

    report = f"🌍 **Alpha Hunter Report**\n(Source: ClubElo)\n\n"
    count = 0
    
    for idx, row in upcoming.iterrows():
        home = row['Home']
        away = row['Away']
        h_elo = row['HomeElo']
        a_elo = row['AwayElo']
        country = row['Country']
        date_str = row['Date'].strftime("%m/%d")
        
        # 승률 계산 (ELO 공식)
        dr = h_elo + 100 - a_elo
        win_prob = 1 / (10**(dr/400) + 1)
        prob_pct = (1 - win_prob) * 100
        
        # 추천 기준: 승률 60% 이상
        if prob_pct >= 60:
            count += 1
            emoji = "🔥" if prob_pct >= 70 else "✅"
            
            report += f"{emoji} **[{country}]** {date_str}\n"
            report += f"⚽ **{home}** vs {away}\n"
            report += f"🧠 승률: **{prob_pct:.1f}%** (ELO차: {int(h_elo - a_elo)})\n"
            report += "------------------\n"

    # 메시지 전송
    if count > 0:
        if len(report) > 4000: report = report[:4000] + "\n...(후략)"
        send_telegram(report)
        print(f"✅ 총 {count}개 경기 전송 완료")
    else:
        send_telegram(f"📉 분석 완료: {today} 기준 추천 경기가 없습니다.")

if __name__ == "__main__":
    run_alpha_hunter()
