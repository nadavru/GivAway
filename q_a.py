from transformers import pipeline


class QuestionAnswering():
    def __init__(self, score_threshold=0.1):
        self.q_a_oracle = pipeline(model="deepset/roberta-base-squad2")
        self.score_threshold = score_threshold
    
    def ask(self, questions, context):
        answers = self.q_a_oracle(question=questions, context=context)
        if not isinstance(questions, list):
            answers = [answers]
        
        returned_answers = []
        for answer in answers:
            score = answer["score"]
            if score>self.score_threshold:
                returned_answers.append(answer["answer"])
            else:
                returned_answers.append(None)
        return returned_answers