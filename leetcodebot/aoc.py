from datetime import UTC, datetime, timedelta
import os
from dataclasses import dataclass

import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

users_by_id = {
    name.split(":")[0]: name.split(":")[1] for name in os.getenv("AOC_USER_IDS", default=":").split(",")
}
token: str = os.getenv("AOC_TOKEN")
leaderboard_id = os.getenv("AOC_LEADERBOARD")


@dataclass
class AOCResult:
    name: str
    stars: int
    local_score: int
    current_day_solutions: int


def get_leaderboard(year: int | None = None) -> list[AOCResult]:
    today = datetime.now(tz=UTC) - timedelta(hours=5)
    year = year or today.year
    check_today = year == today.year and today.month == 12 and today.day < 26

    if len(token) == 0 or len(leaderboard_id) == 0:
        raise Exception("Can't fetch data for the leaderboard")

    url = f"https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json"
    cookies = dict(session=token)
    response = requests.get(url, cookies=cookies)
    if response.status_code != 200:
        raise Exception("Failed to fetch data for the leaderboard")

    data_json = dict(response.json())
    data = data_json.get("members", {})
    results: list[AOCResult] = []
    for identifier in users_by_id:
        user_data = data.get(identifier, {})
        current_day_solutions = 0
        if check_today:
            current_day = user_data.get("completion_day_level", {}).get(f"{today.day}", {})
            current_day_solutions += 1 if current_day.get("1") is not None else 0
            current_day_solutions += 1 if current_day.get("2") is not None else 0

        results.append(
            AOCResult(
                name=users_by_id[identifier],
                stars=user_data.get("stars", 0),
                local_score=user_data.get("local_score", 0),
                current_day_solutions=current_day_solutions
            )
        )
    return sorted(results, key=lambda x: x.stars, reverse=True)


async def send_aoc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        leaderboard = get_leaderboard()
        answer = ""
        nice: list[str] = []
        excellent: list[str] = []
        for user_info in leaderboard:
            answer += f"*{user_info.name}*:\t{user_info.stars} ⭐️\n"
            if user_info.current_day_solutions == 2:
                excellent.append(user_info.name)
            elif user_info.current_day_solutions == 1:
                nice.append(user_info.name)

        if len(nice) > 0:
            answer += f"\nВерим, что дожмут: {", ".join(nice)}."

        if len(excellent) > 0:
            answer += f"\nКрасавчики дня: {", ".join(excellent)}."
        await update.message.reply_text(answer, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"Error occurred\n{str(e)}", parse_mode=ParseMode.MARKDOWN)

