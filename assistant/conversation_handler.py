from assistant import plugin_manager, gpt_caller
from assistant.data_manager import add_to_tokens_count, retrive_history, add_to_history
from assistant.conversation_info_manager import update_bot_sentiment

plugins = plugin_manager.PluginManager()
plugins.initialize_plugins()

def ask_yumi(message: str) -> dict:
    response, tokens = gpt_caller.ask(message)
    output = plugins.process(response)

    if 'SentimentClassification' in output:
        update_bot_sentiment(output['SentimentClassification'])

    add_to_tokens_count(tokens)
    return output

def get_last_message() -> dict:
    responses = retrive_history(1)
    if len(responses) == 0:
        response = 'Good morning meowster, how can I help you?'
        add_to_history('Yumi: ' + response)
    else:
        response = responses[0][6:].strip()
    return {'response': response}