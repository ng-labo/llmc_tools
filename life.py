# llmc_tools/life.py
# 生活関連ツール（天気など）を集約するモジュール
# 将来的に calendar, reminder, stock などもここに追加予定

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"

def weather(location: str) -> dict:
    """指定した場所の現在の天気と今日の簡単な天気予報を取得します。
    気温、降水確率、風、湿度などを確認できます。
    location例: "Tokyo", "Kawasaki", "Hakone"
    """
    print(f"⛅ ? {location}")
    try:
        url = f"https://wttr.in/{location}"
        r = requests.get(
            url,
            params={"format": "j1"},
            headers={"User-Agent": UA},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        current = data["current_condition"][0]

        # 今日
        today = data["weather"][0]

        return {
            "result": "success",
            "location": location,
            "current": {
                "temp_c": current["temp_C"],
                "feels_like_c": current["FeelsLikeC"],
                "weather": current["weatherDesc"][0]["value"],
                "humidity": current["humidity"],
                "wind_kmph": current["windspeedKmph"],
            },
            "today": {
                "max_temp_c": today["maxtempC"],
                "min_temp_c": today["mintempC"],
                "hours": [
                    {
                        "time": h["time"],
                        "weather": h["weatherDesc"][0]["value"],
                        "rain_chance": h["chanceofrain"],
                        "temp_c": h["tempC"],
                    }
                    for h in today["hourly"]
                ],
            },
        }

    except Exception as e:
        return {
            "result": "failed",
            "error": str(e),
        }


FUNCTIONS = {
    "weather": weather,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": (
                "指定した場所の現在の天気と今日の簡単な天気予報を取得します。"
                "気温、降水確率、風、湿度などを確認できます。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "天気を調べる場所。例: Tokyo, Kawasaki, Hakone"
                    }
                },
                "required": ["location"]
            }
        }
    }
]
