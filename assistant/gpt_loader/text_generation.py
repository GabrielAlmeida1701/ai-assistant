import ast
import gc
import time
import torch
import random
import transformers
import assistant.gpt_loader.shared as shared
from assistant.gpt_loader.callbacks import _SentinelTokenStoppingCriteria
from assistant import logger


def set_manual_seed(seed):
    seed = int(seed)
    if seed == -1:
        seed = random.randint(1, 2**31)

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    return seed

def encode(prompt, add_special_tokens=True, add_bos_token=True, truncation_length=None):
    input_ids = shared.tokenizer.encode(str(prompt), return_tensors='pt', add_special_tokens=add_special_tokens, max_length=2024, truncation=True)

    # This is a hack for making replies more creative.
    if not add_bos_token and input_ids[0][0] == shared.tokenizer.bos_token_id:
        input_ids = input_ids[:, 1:]

    # Llama adds this extra token when the first character is '\n', and this
    # compromises the stopping criteria, so we just remove it
    if shared.is_llama_model and input_ids[0][0] == 29871:
        input_ids = input_ids[:, 1:]

    # Handling truncation
    if truncation_length is not None:
        input_ids = input_ids[:, -truncation_length:]

    return input_ids.cuda()

def decode(output_ids, skip_special_tokens=True):
    return shared.tokenizer.decode(output_ids, skip_special_tokens)

def get_reply_from_output_ids(output_ids, input_ids, state):
    new_tokens = len(output_ids) - len(input_ids[0])
    reply = decode(output_ids[-new_tokens:], state['skip_special_tokens'])

    # Prevent LlamaTokenizer from skipping a space
    if shared.is_llama_model and len(output_ids) > 0:
        if shared.tokenizer.convert_ids_to_tokens(int(output_ids[-new_tokens])).startswith('▁'):
            reply = ' ' + reply

    return reply

def generate_reply(request_param: dict) -> str:
    generator = _generate_llama_reply(request_param)
    answer = ''
    for a in generator:
        answer = a

    clear_torch_cache()
    return answer

def _generate_llama_reply(state: dict):
    prompt = state['prompt']
    seed = set_manual_seed(state['seed'])
    stopping_strings = ['\nASSISTANT:', '</s>\nUSER:']
    # clear_torch_cache()

    generate_params = {}
    for k in ['max_new_tokens', 'do_sample', 'temperature', 'top_p', 'typical_p', 'repetition_penalty', 'encoder_repetition_penalty', 'top_k', 'min_length', 'no_repeat_ngram_size', 'num_beams', 'penalty_alpha', 'length_penalty', 'early_stopping']:
        generate_params[k] = state[k]

    for k in ['epsilon_cutoff', 'eta_cutoff']:
        if state[k] > 0:
            generate_params[k] = state[k] * 1e-4
    
    max_prompt_length = state['truncation_length'] - state['max_new_tokens']
    input_ids = encode(prompt, add_bos_token=state['add_bos_token'], truncation_length=max_prompt_length)
    output = input_ids[0]
    eos_token_ids = [shared.tokenizer.eos_token_id] if shared.tokenizer.eos_token_id is not None else []

    generate_params.update({'inputs': input_ids})
    
    # Create the StoppingCriteriaList with the stopping strings (needs to be done after tokenizer extensions)
    stopping_criteria_list = transformers.StoppingCriteriaList()
    for st in (stopping_strings, ast.literal_eval(f"[{state['custom_stopping_strings']}]")):
        if type(st) is list and len(st) > 0:
            sentinel_token_ids = [encode(string, add_special_tokens=False) for string in st]
            stopping_criteria_list.append(_SentinelTokenStoppingCriteria(sentinel_token_ids=sentinel_token_ids, starting_idx=len(input_ids[0])))
            break

    generate_params['eos_token_id'] = eos_token_ids
    generate_params['stopping_criteria'] = stopping_criteria_list
    if not shared.is_llama_model:
        generate_params['pad_token_id'] = 0

    t0 = time.time()
    with torch.no_grad():
        output = shared.model.generate(**generate_params)[0]
        output = output.cuda()
    
    yield get_reply_from_output_ids(output, input_ids, state)

    t1 = time.time()
    logger.info(f'Output generated in {(t1-t0):.2f} seconds (seed {seed})')
    return

def clear_torch_cache():
    gc.collect()
    torch.cuda.empty_cache()