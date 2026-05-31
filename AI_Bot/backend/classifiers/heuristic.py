from backend.classifiers.base import ClassifierStrategy


class HeuristicClassifier(ClassifierStrategy):
    """Classifies based on structural signals in the message.

    Uses message length, sentence count, and connective words
    as proxies for query complexity — no keyword lists required.
    """

    _CONNECTIVES = {"and", "but", "also", "then", "after", "before", "because", "however"}
    _SIMPLE_STARTERS = {"what", "list", "show", "how many", "is there", "are there"}
    _COMPLEX_THRESHOLD_WORDS = 15
    _SIMPLE_THRESHOLD_WORDS  = 6

    def classify(self, user_input: str) -> str:
        text       = user_input.strip().lower()
        words      = text.split()
        word_count = len(words)
        sentences  = [s.strip() for s in text.split(".") if s.strip()]

        if word_count <= self._SIMPLE_THRESHOLD_WORDS:
            return "simple"
        if word_count >= self._COMPLEX_THRESHOLD_WORDS:
            return "complex"
        if len(sentences) > 1:
            return "complex"

        connective_count = sum(1 for w in words if w in self._CONNECTIVES)
        if connective_count >= 2:
            return "complex"

        if any(text.startswith(s) for s in self._SIMPLE_STARTERS):
            return "simple"

        return "complex"  # default
