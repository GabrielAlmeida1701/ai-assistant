class PluginBase():
    def initialize(self):
        pass

    def process(self, gpt_response: str):
        pass

    def cleanup(self):
        pass
    
    def get_priority(self) -> int:
        return 10