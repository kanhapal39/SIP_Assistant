"""TF-IDF retrieval over the curated corpus in data/corpus/.

Each markdown file is one document. Its first "# " heading is the title.
Anything scoring below RELEVANCE_THRESHOLD is treated as "no relevant doc",
which is what drives abstention downstream.
"""

import os
import re
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "corpus")

# Cosine similarity floor for a doc to count as relevant. Set from the golden
# set: lowest in-domain hit is E2 (~0.135), highest out-of-domain is B3
# (~0.115). The margin is thin — re-check it whenever the corpus changes.
RELEVANCE_THRESHOLD = 0.12

# Titles are short and dense with the key terms, so they're weighted up by
# repeating them in the indexed text.
TITLE_WEIGHT = 2


@dataclass
class Doc:
    doc_id: str  # path relative to CORPUS_DIR, e.g. "faq/nav_allocation_timing.md"
    title: str
    body: str


@dataclass
class Hit:
    doc: Doc
    score: float


def load_corpus(corpus_dir: str = CORPUS_DIR) -> List[Doc]:
    docs = []
    for root, _, files in os.walk(corpus_dir):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as f:
                text = f.read().strip()
            lines = text.splitlines()
            if lines and lines[0].startswith("# "):
                title, body = lines[0][2:].strip(), "\n".join(lines[1:]).strip()
            else:
                title, body = os.path.splitext(name)[0], text
            doc_id = os.path.relpath(path, corpus_dir).replace(os.sep, "/")
            docs.append(Doc(doc_id=doc_id, title=title, body=body))
    docs.sort(key=lambda d: d.doc_id)
    return docs


def _tokenize_text(text: str) -> str:
    # Lowercase and strip punctuation so "NAV?" / "nav" / "step-up" all match.
    return re.sub(r"[^a-z0-9%\s]", " ", text.lower())


class Retriever:
    def __init__(self, docs: List[Doc] = None, threshold: float = RELEVANCE_THRESHOLD):
        self.docs = docs if docs is not None else load_corpus()
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(
            preprocessor=_tokenize_text,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        texts = [" ".join([d.title] * TITLE_WEIGHT + [d.body]) for d in self.docs]
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, question: str, k: int = 3) -> List[Hit]:
        """Top-k docs by cosine similarity, highest first (unfiltered)."""
        scores = cosine_similarity(self.vectorizer.transform([question]), self.matrix)[0]
        ranked = sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)[:k]
        return [Hit(doc=self.docs[i], score=float(scores[i])) for i in ranked]

    def retrieve(self, question: str, k: int = 1) -> List[Hit]:
        """Top-k docs that clear the relevance threshold; empty means abstain."""
        return [h for h in self.search(question, k=k) if h.score >= self.threshold]
