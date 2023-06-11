from datetime import datetime
from assistant.data_manager import load_settings, save_settings
from assistant.plugin_manager import PluginManager

datetime_format = "%Y-%m-%d %H:%M"
user_info = load_settings('user_info')

def fill_user_info(prompt: str) -> str:
    prompt = prompt.format(
        user_sentiment=user_info['user_sentiment'],
        last_message=time_difference(),
        current_date=datetime.now().strftime(datetime_format)
    )
    #TODO: birthday

def update_bot_sentiment(sentiment: str):
    user_info['bot_sentiment'] = sentiment
    save_settings('user_info', user_info)

def update_last_message(user_input: str):
    if user_input == '_HIATUS_':
        return
    
    user_info['user_sentiment'] = PluginManager().execute_plugin('SentimentClassification', user_input, 'neutral')
    user_info['last_message'] = datetime.now().strftime("%m/%d/%Y %H:%M")
    save_settings('user_info', user_info)

def time_difference():
    start_datetime = datetime.strptime(user_info['last_message'], datetime_format)
    end_datetime = datetime.now()

    time_difference = end_datetime - start_datetime

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    result = ""
    if days > 0:
        result += f"{days} day{'s' if days > 1 else ''}"

    if hours > 0:
        result += f"{', ' if result != '' else ''}{hours} hour{'s' if hours > 1 else ''}"

    if minutes > 0:
        result += f"{', ' if result != '' else ''}{minutes} minute{'s' if minutes > 1 else ''}"

    if seconds > 0 or result == "":
        result += f"{', ' if result != '' else ''}{seconds} second{'s' if seconds > 1 else ''}"