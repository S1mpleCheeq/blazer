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
    def embedding_model(self):
        return self._config['llm']['embedding_model']

    @property
    def max_nodes(self):
        return self._config['task']['max_nodes']

    @property
    def priority_keywords(self):
        return self._config['task']['priority_keywords']

    @property
    def router_strategy(self):
        return self._config['router']['strategy']

    @property
    def router_top_k(self):
        return self._config['router']['top_k']

config = Config()
