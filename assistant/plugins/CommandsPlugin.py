from assistant.models.PluginBase import PluginBase
from assistant.plugins.commands import run_program, alarm, update_model

class CommandsPlugin(PluginBase):
    def process(self, response: str):
        if '<run\_program>' in response or '<run_program>' in response:
            run_program.execute(self.get_args(response))

        elif '<update\_model>' in response or '<update_model>' in response:
            update_model.execute(self.get_args(response))
        
        elif '<alarm>' in response:
            alarm.execute(self.get_args(response))
    
    def get_args(self, command):
        args = command.replace('>', '').split('<')
        args.pop(0)
        return args