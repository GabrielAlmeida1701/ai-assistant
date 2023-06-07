import re
import threading
from google.cloud import texttospeech as tts
from elevenlabs import generate, play, set_api_key
from assistant.models.PluginBase import PluginBase
from assistant.data_manager import load_plugin_settings
from assistant import logger

class TextToSpeach(PluginBase):
    def get_priority(self) -> int:
        return 0

    def initialize(self):
        settings = load_plugin_settings('tts')
        self.use_elevenlabs = settings['use_elevenlabs']
        self.enabled = settings['enabled']

        if not self.enabled:
            return

        if self.use_elevenlabs:
            logger.info('Using ElevenLabs TTS')
            set_api_key('b22f0bb3295ed10e46a3c836a797990d')
        else:
            logger.info('Using Google TTS')
            self.client = tts.TextToSpeechClient.from_service_account_file("./resources/key.json")
            self.voice = tts.VoiceSelectionParams(
                language_code="en-US",
                ssml_gender=tts.SsmlVoiceGender.FEMALE
            )
            self.voice.name = 'en-GB-Wavenet-A'
            self.audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)
            self.audio_config.pitch = -.4
            self.audio_config.speaking_rate = 1.19

    def process(self, gpt_response: str):
        if not self.enabled:
            return
            
        input = self.clean_text(gpt_response)
        if len(input) <= 2:
            return

        if self.use_elevenlabs:
            thread = threading.Thread(target=self.call_elevenlabs, args=(input, None))
        else:
            thread = threading.Thread(target=self.call_google, args=(input, None))
        thread.start()
    
    def call_elevenlabs(self, input: str, arg2):
        try:
            audio = generate(
                text=input,
                voice="ZZ4YtKKuT7ZvirENWjI2",
                model="eleven_monolingual_v1"
            )
            play(audio)
        except Exception as e:
            logger.error(f'[YUMIAI] ElevenLabs Error: {str(e)}')
    
    def call_google(self, input:str, arg2):
        synthesis_input = tts.SynthesisInput(ssml=f'<speak>{input}</speak>')
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice,
            audio_config=self.audio_config
        )
        play(response.audio_content)

    def clean_text(self, gpt_response: str) -> str:
        val = re.sub("<.*?>", "", gpt_response)
        val = re.sub("\*.*?\*", "", gpt_response)
        val = re.sub(r'\s+', ' ', val)
        val = val.replace(':3', '').replace(':)', '').replace(':D', '').replace(':(', '')
        val = val.replace('plz', 'please')
        val = re.sub("\bnp\b", "no problem", val)
        val = val.replace('^^', '')
        val = val.replace('<3', '')
        return f'"{val.strip()}"'