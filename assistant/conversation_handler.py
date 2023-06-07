import json
from assistant import plugin_manager, gpt_caller
from assistant.data_manager import add_to_tokens_count, retrive_history, add_to_history

plugins = plugin_manager.PluginManager()
plugins.initialize_plugins()

def ask_yumi(message: str) -> str:
    response, tokens = gpt_caller.ask(message)
    output = plugins.process(response)
    add_to_tokens_count(tokens)
    return output

def get_last_message() -> str:
    responses = retrive_history(1)
    if len(responses) == 0:
        response = 'Good morning meowster, how can I help you?'
        add_to_history('Yumi: ' + response)
    else:
        response = responses[0][6:].strip()
    return json.dumps({'response': response})