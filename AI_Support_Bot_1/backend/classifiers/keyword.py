from backend.classifiers.base import ClassifierStrategy


class KeywordClassifier(ClassifierStrategy):
    """Classifies based on presence of known keywords.

    Simple if simple keywords dominate with no complex signals.
    Defaults to "complex" when uncertain — safer to over-provision.
    """

    _SIMPLE = {
        "hi", "hello", "hey", "thanks", "thank you", "bye",
        "list", "show", "what challenges", "what projects",
        "what is", "how many", "pricing", "cost", "free",
        "available", "options",
    }

    _COMPLEX = {
        "recommend", "suggest", "best for", "should i", "which one",
        "learning path", "roadmap", "sequence", "order", "progress", "after",
        "compare", "difference", "vs", "better",
        "why", "explain", "how does", "help me decide",
        "want to learn", "interested in", "experience",
        "distributed", "advanced", "beginner", "start",
    }

    def classify(self, user_input: str) -> str:
        text = user_input.lower()

        has_simple  = any(kw in text for kw in self._SIMPLE)
        has_complex = any(kw in text for kw in self._COMPLEX)

        if has_complex:
            return "complex"
        if has_simple and not has_complex:
            return "simple"
        return "complex"  # default — safer to over-provision
