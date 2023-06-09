import json
from assistant import logger, gpt_caller, conversation_handler
from assistant.models.DBConnector import DBConnector
from assistant.gpt_loader import shared

db = DBConnector()

def load_settings(sfile: str):
    with open(f'./data/{sfile}.json', 'r') as file:
        data = json.load(file)
    return data

def save_settings(sfile: str, data):
    with open(f'./data/{sfile}.json', 'w') as file:
        json.dump(data, file, indent=4)

    if sfile == 'general':
        if gpt_caller.use_api != data['use_api']:
            logger.warning('Model reload not implemented')
        gpt_caller.load_settings_bot()
    elif sfile == 'llm':
        if shared.model_name != data['model']:
            logger.warning('Model reload not implemented')
        gpt_caller.load_settings_bot()
    elif sfile == 'plugins':
        conversation_handler.plugins.initialize_plugins()

def load_plugin_settings(settings_key: str):
    data = load_settings('plugins')
    if settings_key not in data:
        data[settings_key] = { 'enabled': True }
        save_settings('plugins', data)
    return data[settings_key]

def save_prompt(prompt: str):
    try:
        with open(f'./resources/prompt.txt', 'w') as file:
            file.write(prompt)
            file.close()
    except Exception as e:
        logger.error(f'Error while saving prompt: {str(e)}')

def retrive_history(limit: int = 30) -> list[str]:
    return db.retrive_history(limit)

def add_to_history(message: str):
    db.add_to_history(message)

def add_to_tokens_count(tokens: int):
    with open('./data/tokens.txt', 'r+') as file:
        val = int(file.readline())
        total = val + tokens
        file.seek(0)
        file.write(str(total))
        file.truncate()
