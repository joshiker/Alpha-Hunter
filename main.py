import requests
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 🔐 설정 로드 (깃허브 금고에서 꺼내옴)
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
API_KEY = os.environ.get("FOOTBALL_DATA_TOKEN")

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 텔레그램 설정이 없습니다.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def run_alpha_hunter():
    print("🚀 Alpha Hunter: Official API Mode 가동...")

    if not API_KEY:
        print("❌ FOOTBALL_DATA_TOKEN이 없습니다. Secrets를 확인하세요.")
        return

    # 1. 5대 리그 코드 (PL:프리미어리그, PD:라리가, BL1:분데스리가, SA:세리에A, FL1:리그1)
    leagues = ['PL', 'PD', 'BL1', 'SA', 'FL1']
    
    # 2. 날짜 설정 (오늘 ~ 3일 뒤)
    today = datetime.now().date()
    date_to = today + timedelta(days=3)
    
    headers = {'X-Auth-Token': API_KEY}
    all_matches = []

    # 3. 리그별 데이터 수집
    for league in leagues:
        url = f"https://api.football-data.org/v4/competitions/{league}/matches"
        params = {
            'dateFrom': today.strftime('%Y-%m-%d'),
            'dateTo': date_to.strftime('%Y-%m-%d')
        }
        
        try:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                matches = data.get('matches', [])
                all_matches.extend(matches)
            else:
                print(f"⚠️ {league} 조회 실패: {res.status_code}")
        except Exception as e:
            print(f"에러 발생: {e}")

    if not all_matches:
        send_telegram(f"💤 {today}~{date_to} 기간에 예정된 5대 리그 경기가 없습니다.")
        return

    # 4. 리포트 작성
    report = f"🌍 **Alpha Hunter Official**\n({today} ~ {date_to})\n\n"
    count = 0
    
    # 강팀 리스트 (간단한 파워 랭킹 필터)
    top_teams = [
        'Man City', 'Liverpool', 'Arsenal', 'Real Madrid', 'Barcelona', 
        'Bayern Munich', 'Leverkusen', 'Inter', 'Juventus', 'PSG'
    ]

    for match in all_matches:
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        league_name = match['competition']['name']
        utc_date = match['utcDate'] # 2026-01-31T15:00:00Z 형식
        
        # 시간 변환 (UTC -> 한국시간 KST)
        match_time = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=9)
        time_str = match_time.strftime("%m/%d %H:%M")
        
        # 빅매치나 강팀 경기만 알림 (너무 많이 오는 것 방지)
        is_big_game = any(t in home for t in top_teams) or any(t in away for t in top_teams)
        
        if is_big_game:
            count += 1
            report += f"🏆 **[{league_name}]**\n"
            report += f"⚽ **{home}** vs {away}\n"
            report += f"⏰ {time_str} (KST)\n"
            report += "------------------\n"

    # 전송
    if count > 0:
        if len(report) > 4000: report = report[:4000]
        send_telegram(report)
        print(f"✅ 총 {count}개 경기 전송 완료")
    else:
        send_telegram("📉 기간 내 주목할 만한 빅매치가 없습니다.")

if __name__ == "__main__":
    run_alpha_hunter()
