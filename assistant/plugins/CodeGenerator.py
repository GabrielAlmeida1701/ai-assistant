from assistant.gpt_caller import generate_reply
from assistant.models.PluginBase import PluginBase

class CodeGenerator(PluginBase):
    def process(self, gpt_response: str):
        #use execute_generator in varius steps to gather info to generate the code
        pass