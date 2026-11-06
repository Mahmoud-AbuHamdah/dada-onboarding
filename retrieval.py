import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Arabic diacritics (harakat) to remove
DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670]")


def normalize_ar(text):
    """Rewrite Arabic text into one standard form so spellings match."""
    text = str(text)
    text = DIACRITICS.sub("", text)           # remove diacritics
    text = text.replace("\u0640", "")         # remove tatweel (ـ)
    text = re.sub("[إأآا]", "ا", text)        # all alef forms -> ا
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = text.replace("ؤ", "و").replace("ئ", "ي")
    text = re.sub(r"[^\w\s]", " ", text)      # remove punctuation
    text = re.sub(r"\s+", " ", text)          # collapse spaces
    return text.strip().lower()               # lower() is for English words


class KeywordRetriever:
    """Finds the knowledge base facts most similar to a question."""

    def __init__(self, kb):
        self.kb = kb.reset_index(drop=True)

        # Each fact is searched using its Arabic text, topic and English keyword
        docs = (
            self.kb["answer_ar"] + " " + self.kb["topic"] + " " + self.kb["keyword_en"]
        ).map(normalize_ar)

        # Character pieces of 2-4 letters, within word boundaries
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.matrix = self.vectorizer.fit_transform(docs)

    def search(self, question, top_k=3):
        """Return the top_k most similar facts, best first."""
        q_vec = self.vectorizer.transform([normalize_ar(question)])
        scores = cosine_similarity(q_vec, self.matrix)[0]
        best = scores.argsort()[::-1][:top_k]   # indexes of the highest scores

        results = []
        for i in best:
            row = self.kb.iloc[i]
            results.append({
                "id": row["id"],
                "text": row["answer_ar"],
                "score": float(scores[i]),
                "source": f"{row['source_document']}, p. {row['source_page']}",
            })
        return results