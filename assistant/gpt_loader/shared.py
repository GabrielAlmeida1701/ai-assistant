import transformers

model: transformers.LlamaForCausalLM = None
tokenizer = None
stop_everything = False
is_llama_model = False