import speech_recognition as sr

class Listener():
    def __init__(self):
        # Initialize the recognizer
        self.r = sr.Recognizer()
    
    def listen(self):

        while(1):
            
            try:
                
                with sr.Microphone() as source2:
                    
                    self.r.adjust_for_ambient_noise(source2, duration=0.2)
                    
                    #listens for the user's input
                    audio2 = self.r.listen(source2)
                    
                    # Using google to recognize audio
                    MyText = self.r.recognize_google(audio2)
                    
                    return MyText
                    
            except sr.RequestError as e:
                continue
                print("Could not request results; {0}".format(e))
                
            except sr.UnknownValueError:
                continue
                print("unknown error occurred")