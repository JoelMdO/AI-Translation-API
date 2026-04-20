# -------------------------
# tokenizer — word-count approximation
# transformers/torch are not installed; words * 1.3 is sufficient for chunk budgeting
# -------------------------

class AyaTokenizer:

    def __init__(self):
        self.mode = "fallback"

    def count(self, text: str) -> int:
        return int(len(text.split()) * 1.3)
