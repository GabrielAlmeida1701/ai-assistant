from datetime import datetime
from assistant.data_manager import load_settings, save_settings
from assistant.plugin_manager import PluginManager

datetime_format = "%m/%d/%Y %H:%M"
info = load_settings('conversation_info')

def fill_user_info(prompt: str) -> str:
    current_date = datetime.now().strftime('%m/%d/%Y') + ' ' + datetime.now().strftime('%A')

    return prompt.format(
        user_sentiment=info['user_sentiment'],
        last_message=time_difference(),
        current_date=current_date
    )

def update_bot_sentiment(sentiment: str):
    info['bot_sentiment'] = sentiment
    save_settings('conversation_info', info)

def update_last_message(user_input: str):
    if user_input == '_HIATUS_':
        return
    
    info['user_sentiment'] = PluginManager().execute_plugin('SentimentClassification', user_input, 'neutral')
    info['last_message'] = datetime.now().strftime(datetime_format)
    save_settings('conversation_info', info)

def time_difference():
    start_datetime = datetime.strptime(info['last_message'], datetime_format)
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
    return result