from assistant.gpt_caller import generate_reply
from assistant.models.PluginBase import PluginBase

class CodeGenerator(PluginBase):
    def process(self, gpt_response: str):
        #call openai, in the promp send relevant files for the generation
        #token limit: 8k
        pass