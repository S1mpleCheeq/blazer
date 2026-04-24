import json
import os


class Config:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

    @property
    def llm_model(self):
        return self._config['llm']['model']

    @property
    def max_nodes(self):
        return self._config['task']['max_nodes']

    @property
    def battery_threshold(self):
        return self._config['dogs']['battery_threshold']

    @property
    def drain_run(self):
        return self._config['dogs']['drain_run']

    @property
    def drain_photo(self):
        return self._config['dogs']['drain_photo']

    @property
    def charging_seconds(self):
        return self._config['dogs']['charging_seconds']


config = Config()
