import re

def replace_with(text, replaces):
    final_text = text.lower()
    for from_word, to_word in replaces:
        pattern = rf'(?<![a-zA-Z]){from_word}(?![a-zA-Z])'
        final_text = re.sub(pattern, to_word, final_text)
    return final_text