from transformers import pipeline

class SentimentClassifier():
    def __init__(self):
        self.distilled_student_sentiment_classifier = pipeline(
            model="lxyuan/distilbert-base-multilingual-cased-sentiments-student", 
            return_all_scores=True
        )
    
    def classify(self, text):
        output = self.distilled_student_sentiment_classifier(text)[0]
        positive = output[0]
        assert positive["label"] == "positive"
        negative = output[2]
        assert negative["label"] == "negative"

        return positive["score"] > negative["score"]