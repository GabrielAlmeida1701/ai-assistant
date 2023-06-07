import gc
import sys
import time
import inspect
from pathlib import Path

import torch
import transformers
from transformers import AutoConfig, LlamaTokenizer, AutoModelForCausalLM, AutoTokenizer

import assistant.gpt_loader.shared as shared
from assistant.data_manager import load_settings
from assistant import logger

sys.path.insert(0, str(Path("F:/Bibliotecas/Documentos/AI/oobabooga_windows/text-generation-webui/repositories/GPTQ-for-LLaMa")))

try:
    import llama_inference_offload
except ImportError:
    logger.error('Failed to load GPTQ-for-LLaMa')
    logger.error('See https://github.com/oobabooga/text-generation-webui/blob/main/docs/GPTQ-models-(4-bit-mode).md')
    sys.exit(-1)

try:
    from modelutils import find_layers
except ImportError:
    from utils import find_layers

try:
    from quant import make_quant
    is_triton = False
except ImportError:
    import quant
    is_triton = True

def _load_quant(model, checkpoint, wbits, groupsize=-1, faster_kernel=False, exclude_layers=None, kernel_switch_threshold=128, eval=True):
    exclude_layers = exclude_layers or ['lm_head']

    def noop(*args, **kwargs):
        pass

    config = AutoConfig.from_pretrained(model, trust_remote_code=False)
    torch.nn.init.kaiming_uniform_ = noop
    torch.nn.init.uniform_ = noop
    torch.nn.init.normal_ = noop

    torch.set_default_dtype(torch.half)
    transformers.modeling_utils._init_weights = False
    torch.set_default_dtype(torch.half)
    model = AutoModelForCausalLM.from_config(config, trust_remote_code=False)
    torch.set_default_dtype(torch.float)
    if eval:
        model = model.eval()

    layers = find_layers(model)
    for name in exclude_layers:
        if name in layers:
            del layers[name]

    gptq_args = inspect.getfullargspec(make_quant).args

    make_quant_kwargs = {
        'module': model,
        'names': layers,
        'bits': wbits,
    }
    if 'groupsize' in gptq_args:
        make_quant_kwargs['groupsize'] = groupsize
    if 'faster' in gptq_args:
        make_quant_kwargs['faster'] = faster_kernel
    if 'kernel_switch_threshold' in gptq_args:
        make_quant_kwargs['kernel_switch_threshold'] = kernel_switch_threshold

    make_quant(**make_quant_kwargs)

    try:
        del layers
        if checkpoint.endswith('.safetensors'):
            from safetensors.torch import load_file as safe_load
            model.load_state_dict(safe_load(checkpoint), strict=False)
        else:
            model.load_state_dict(torch.load(checkpoint), strict=False)
    except Exception as e:
        print(str(e))
        raise e

    model.seqlen = 2048
    model.to(torch.device('cuda:0'))
    return model

def find_quantized_model_file(path_to_model: Path):
    for ext in ['.pt', '.safetensors']:
        found = list(path_to_model.glob(f"*{ext}"))
        if len(found) > 0:
            if len(found) > 1:
                logger.warning(f'More than one {ext} model has been found. The last one will be selected. It could be wrong.')

            pt_path = found[-1]
            break
    return pt_path

def load_model():
    settings = load_settings('llm')
    # model_name = 'TheBloke_vicuna-13B-1.1-GPTQ-4bit-128g'
    # model_name = 'mayaeary_pygmalion-6b_dev-4bit-128g'
    # model_name = 'notstoic_pygmalion-13b-4bit-128g'
    model_name = settings['model']

    t0 = time.time()
    model_dir = f'F:/Bibliotecas/Documentos/AI/oobabooga_windows/text-generation-webui/models/{model_name}'
    path_to_model = Path(model_dir)
    pt_path = find_quantized_model_file(path_to_model)
    shared.is_llama_model = type(shared.model) is transformers.LlamaForCausalLM
    threshold = 128 if shared.is_llama_model else False

    logger.info(f"Loading model {model_name}")
    shared.model = _load_quant(str(path_to_model), str(pt_path), 4, 128, kernel_switch_threshold=threshold)
    shared.model_name = model_name
    logger.info(f'Model loaded {time.time() - t0:.4f}s')

    logger.info("Loading tokenizer")
    if shared.is_llama_model:
        shared.tokenizer = LlamaTokenizer.from_pretrained(path_to_model, clean_up_tokenization_spaces=True)
        shared.tokenizer.eos_token_id = 2
        shared.tokenizer.bos_token_id = 1
        shared.tokenizer.pad_token_id = 0
    else:
        shared.tokenizer = AutoTokenizer.from_pretrained(path_to_model, trust_remote_code=False)
    logger.info('Tokenizer loaded')

def clear_torch_cache():
    gc.collect()
    torch.cuda.empty_cache()