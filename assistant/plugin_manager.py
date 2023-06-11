import os
import importlib.util
from assistant.models.PluginBase import PluginBase

class PluginManager():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_plugins()
        return cls._instance

    def discover_plugins(self):
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        plugin_modules = []

        for file_name in os.listdir(plugin_dir):
            if file_name.endswith(".py") and file_name != "__init__.py":
                module_name = file_name[:-3]  # Remove the ".py" extension
                module_path = os.path.join(plugin_dir, file_name)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugin_modules.append((module, module_name))

        return plugin_modules

    def load_plugins(self):
        plugin_modules = self.discover_plugins()
        plugins: list[PluginBase] = []

        for (module, module_name) in plugin_modules:
            if hasattr(module, "PluginBase"):
                plugin_class = getattr(module, module_name)
                plugin = plugin_class()
                plugins.append(plugin)

        plugins.sort(key=lambda x: x.get_priority())
        self.plugins_map: dict[str, PluginBase] = {
            type(plugin).__name__: plugin
            for plugin in plugins
        }

    def initialize_plugins(self):
        for plugin in self.plugins_map.values():
            plugin.initialize()
    
    def process(self, gpt_response: str) -> str:
        output = { 'response': gpt_response }
        for name, plugin in self.plugins_map.items():
            result = plugin.process(gpt_response)
            if result is not None:
                output[name] = result
        return output

    def execute_plugin(self, plugin_name: str, input: str, default = None):
        if plugin_name in self.plugins_map:
            plugin = self.plugins_map[plugin_name]
            return plugin.process(input)
        return default