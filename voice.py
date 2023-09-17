import pyttsx3


class SpeakText():
    def __init__(self, male=False):
        self.engine = pyttsx3.init()
        voice = self.engine.getProperty('voices')
        if male:
            self.engine.setProperty('voice', voice[0].id)
        else:
            self.engine.setProperty('voice', voice[1].id)
    
    def speak(self, command):
        self.engine.say(command)
        self.engine.runAndWait()

def speak(command, male_voice=False):
    speaker = SpeakText(male_voice)
    speaker.speak(command)
