import os
import telebot
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)


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
    for username in usernames:
        try:
            rank = get_leetcode_user_rank(username)
            user_ranks[username] = rank
        except Exception as e:
            user_ranks[username] = str(e)
    return user_ranks
    

@bot.message_handler(commands=['start', 'rank'])
def send_rank(message):
    usernames = ['sivykh', 'dfomin', 'grafnick', 'gregzhadko', 'kulizhnikov', 'drunstep', 'ptatarintsev', 'dmitryae']
    user_ranks = get_ranks_for_users(usernames)
    sorted_users = sorted(user_ranks.items(), key=lambda item: item[1])
    answer = '```Standings\n'
    for user in sorted_users:
        answer += f'{user[0]}\t{user[1]}\n'
    answer += '```'
    bot.reply_to(message, answer, parse_mode="Markdown")



bot.infinity_polling()
