import torch
import time
from transformers import pipeline
from assistant.models.PluginBase import PluginBase
from assistant.data_manager import load_plugin_settings
from assistant import logger

# 'nateraw/bert-base-uncased-emotion' Very limited
# 'joeddav/distilbert-base-uncased-go-emotions-student' A lot more

class SentimentClassification(PluginBase):
    def initialize(self):
        settings = load_plugin_settings('classify')
        self.enabled = settings['enabled']
        
        if not self.enabled:
            return

        device = torch.device('cuda:0')
        torch_dtype = torch.float16

        if hasattr(self, 'classification_pipe'):
            del self.classification_pipe

        t0 = time.time()
        logger.info('Initializing a sentiment classification pipeline')
        self.classification_pipe = pipeline(
            "text-classification",
            model=settings['model'],
            top_k=None,
            device=device,
            torch_dtype=torch_dtype
        )
        logger.info(f'Sentiment classification pipeline loaded in {time.time() - t0}s')

    def process(self, gpt_response: str):
        if not self.enabled:
            return 'neutral'

        output = self.classification_pipe(
            gpt_response,
            truncation=True,
            max_length=self.classification_pipe.model.config.max_position_embeddings
        )[0]
        sentimests = sorted(output, key=lambda x: x['score'], reverse=True)
        return sentimests[0]['label']