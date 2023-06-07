import re
import requests
import tiktoken
from typing import Any
from assistant.models.gpt_char_info import context, bot_name, example_dialog
from assistant.data_manager import load_settings, retrive_history, add_to_history, save_prompt
from assistant import logger


HOST = 'localhost:5000'
URI = f'http://{HOST}/api/v1/generate'

llm_settings: dict[str, Any] = load_settings('llm')
general_settings: dict[str, Any] = load_settings('general')
# history: list[str] = load_settings('history')
bot_prefix = bot_name + ': '
bot_name_len = len(bot_name)
use_api: bool = general_settings['use_api']
emoji_pattern = re.compile('[\U0001F300-\U0001F64F'
                            '\U0001F680-\U0001F6FF'
                            '\u2600-\u26FF\u2700-\u27BF]+', 
                            flags=re.UNICODE)

def get_generation_params(prompt: str) -> dict:
    stopping_strings = [ 'User:', 'user:' ]
    temperature = float(llm_settings['temperature']) if isinstance(llm_settings['temperature'], str) else llm_settings['temperature']
    top_p = float(llm_settings['top_p']) if isinstance(llm_settings['top_p'], str) else llm_settings['top_p']
    repetition_penalty = float(llm_settings['repetition_penalty']) if isinstance(llm_settings['repetition_penalty'], str) else llm_settings['repetition_penalty']

    return {
        'prompt': prompt,
        'max_new_tokens': llm_settings['max_new_tokens'],
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'repetition_penalty': repetition_penalty,
        'encoder_repetition_penalty': 1.0,
        'top_k': 40,
        'min_length': 3,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,
        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'custom_stopping_strings': stopping_strings,
        'stopping_strings': stopping_strings
    }

def call_api(request_param: dict) -> str:
    response = requests.post(URI, json=request_param)

    if response.status_code == 200:
        result = response.json()
        text = result['results'][-1]['text']
        return text

def num_tokens_from_messages(messages: list[str]) -> int:
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo-0301')
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        num_tokens += len(encoding.encode(message))
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

def remove_emojis(text: str) -> str:
    emoji_mapping = {
        '\ude0a': '',
        '\ud83d': '',
        '\u2764': '',
        '\ufe0f': ''
    }
    output = emoji_pattern.sub(lambda match: emoji_mapping.get(match.group(0), match.group(0)), text)
    return re.sub(r'[\U0001F000-\U0001FFFF]', '', output)

def clean_response(response: str) -> str:
    response = remove_emojis(response)
    if not response.startswith(bot_prefix):
        response = bot_prefix + response
    
    stop_index = response.find('User:')
    if stop_index != -1:
        response = response[:stop_index]

    response = response.replace('\^\^', '^^')

    return response

def write_default_prompt(user_input: str):
    history = retrive_history()
    concat_history = '\n'.join(history)

    return f"""{context}
{example_dialog}
<START>
{concat_history}
User: {user_input}
"""

def build_prompt(user_input: str):
    prompt = write_default_prompt(user_input)
    prompt = remove_emojis(prompt)

    tokens_count = num_tokens_from_messages([prompt])
    return prompt, tokens_count


if use_api:
    logger.info('Using Oobabooga API')
    generator = call_api
else:
    logger.info('Using internal LLM')
    from assistant.gpt_loader import model_loader, text_generation
    model_loader.load_model()
    generator = text_generation.generate_reply

def generate_reply(prompt: str) -> str:
    generation_params = get_generation_params(prompt)
    return generator(generation_params)

def ask(user_input: str) -> tuple[str, int]:
    user_input = user_input.strip()
    prompt, tokens_count = build_prompt(user_input)
    
    while tokens_count >= llm_settings['max_memory_tokens']:
        logger.error("[ERROR] This should not happen: tokens_count >= settings['max_memory_tokens']")

    logger.info(f'Total tokens: {tokens_count}')
    save_prompt(prompt)
    response = clean_response(generate_reply(prompt))
    if not general_settings['test_mode']:
        add_to_history(f'User: {user_input}')
        add_to_history(response)

    logger.info(f'Question: {user_input}')
    logger.info(f'Response: {response}')
    return response[6:].strip(), tokens_count