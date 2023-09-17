from transformers import pipeline

text = "summarize: Yes, I sustained injuries to my neck and back. It really hurts."

summarizer = pipeline("summarization", model="stevhliu/my_awesome_billsum_model")
answer = summarizer(text, max_length=30)

print(answer)