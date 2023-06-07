import speech_recognition as sr

audio_file = "F:/Bibliotecas/Documentos/AI/ai-assistant/resources/myaudio.wav"

# Initialize the recognizer 
r = sr.Recognizer() 

with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source) 
    print('say something')
    audio = r.listen(source)

# result = r.recognize_google(audio, show_all=True) 
# result = r.recognize_whisper(audio)
# print(result)