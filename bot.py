import os
import telebot
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

usernames = ['sivykh', 'dfomin', 'grafnick', 'gregzhadko', 'kulizhnikov', 'drunstep', 'ptatarintsev', 'dmitryae']


########################## RANK COMMAND ##########################

def get_leetcode_user_rank(username):
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            profile {
                ranking
            }
        }
    }
    """
    variables = {
        "username": username
    }
    json_data = {
        "query": query,
        "variables": variables
    }
    response = requests.post(url, json=json_data)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for user {username}")
    
    data = response.json()
    if 'errors' in data:
        raise Exception(f"Error fetching data for user {username}: {data['errors']}")
    
    ranking = data['data']['matchedUser']['profile']['ranking']
    
    if ranking is None:
        return "Unranked"
    return ranking


def get_ranks_for_users(usernames):
    user_ranks = {}
    with ThreadPoolExecutor(max_workers=len(usernames)) as executor:
        future_to_username = {executor.submit(get_leetcode_user_rank, username): username for username in usernames}

        for future in as_completed(future_to_username):
            username = future_to_username[future]
            try:
                result = future.result()
                user_ranks[username] = result
            except Exception as exc:
                user_ranks[username] = str(e)

    return user_ranks
    

@bot.message_handler(commands=['start', 'rank'])
def send_rank(message):
    user_ranks = get_ranks_for_users(usernames)
    sorted_users = sorted(user_ranks.items(), key=lambda item: item[1])
    answer = '```Standings\n'
    for user in sorted_users:
        answer += f'{user[0]}\t{user[1]}\n'
    answer += '```'
    bot.reply_to(message, answer, parse_mode="Markdown")


########################## TODAY COMMAND ##########################

def get_leetcode_daily_challenge():
    url = "https://leetcode.com/graphql"
    query = """
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            date
            userStatus
            link
            question {
                acRate
                difficulty
                freqBar
                frontendQuestionId: questionFrontendId
                isFavor
                paidOnly: isPaidOnly
                status
                title
                titleSlug
                hasVideoSolution
                hasSolution
                topicTags {
                    name
                    id
                    slug
                }
            }
        }
    }
    """
    json_data = {
        "query": query,
        "operationName": "questionOfToday"
    }
    
    response = requests.post(url, json=json_data)
    
    if response.status_code != 200:
        raise Exception("Failed to fetch data from LeetCode")
    
    data = response.json()
    
    if 'errors' in data:
        raise Exception(f"Error fetching data: {data['errors']}")
    
    daily_challenge = data['data']['activeDailyCodingChallengeQuestion']
    
    return daily_challenge


@bot.message_handler(commands=['today'])
def send_today(message):
    try:
        daily_challenge = get_leetcode_daily_challenge()
        question = daily_challenge['question']
        answer = ""
        answer += f"*Title*: {question['title']}\n"
        answer += f"*Difficulty*: `{question['difficulty']}`\n"
        answer += f"*Link*: https://leetcode.com{daily_challenge['link']}\n"
        answer += f"*Acceptance Rate*: {question['acRate']:.2f}%\n"
        
        bot.reply_to(message, answer, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Не получилось\n{str(e)}", parse_mode="Markdown")


########################## STATUS COMMAND ##########################

def solved_today(username, title_slug):
    url = "https://leetcode.com/graphql"
    query = """
    query recentAcSubmissions($username: String!) {
        recentAcSubmissionList(username: $username, limit: 20) {
            titleSlug
            timestamp
        }
    }
    """
    variables = {
        "username": username
    }
    json_data = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(url, json=json_data)
    
    if response.status_code != 200:
        raise Exception("Failed to fetch data from LeetCode")
    
    data = response.json()
    
    if 'errors' in data:
        raise Exception(f"Error fetching data: {data['errors']}")
        
    now_utc = datetime.now(pytz.utc)
    start_of_today_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=pytz.utc)
    timestamp = int(start_of_today_utc.timestamp())
    
    array = data['data']['recentAcSubmissionList']
    last_solved = [x for x in array if int(x.get('timestamp')) > timestamp]
    
    return any(d['titleSlug'] == title_slug for d in last_solved), len(last_solved) > 0


@bot.message_handler(commands=['status'])
def send_today(message):
    try:
        daily_challenge = get_leetcode_daily_challenge()
        question = daily_challenge['question']
        answer = ""
        
        with ThreadPoolExecutor(max_workers=len(usernames)) as executor:
            future_to_username = {executor.submit(solved_today, username, question['titleSlug']): username for username in usernames}

            for future in as_completed(future_to_username):
                username = future_to_username[future]
                try:
                    solved, another = future.result()
                    answer += f'{"✅" if solved else ("☑️" if another else "⬜️")}\t{username}\n'
                except Exception as exc:
                    answer += f'⛔️\t{username}\n'
        
        bot.reply_to(message, answer, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Не получилось\n{str(e)}", parse_mode="Markdown")


########################## MAIN ##########################

if __name__ == "__main__":
    bot.infinity_polling()
