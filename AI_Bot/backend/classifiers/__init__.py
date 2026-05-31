from backend.classifiers.base import ClassifierStrategy
from backend.classifiers.keyword import KeywordClassifier
from backend.classifiers.heuristic import HeuristicClassifier
from backend.classifiers.llm import LLMClassifier

# Classifier registry — all available strategies.
# To add a new strategy:
#   1. Create backend/classifiers/<name>.py implementing ClassifierStrategy
#   2. Import and add it here
STRATEGIES = {
    "keyword":   KeywordClassifier,
    "heuristic": HeuristicClassifier,
    "llm":       LLMClassifier,
}

# Active strategy — currently hardcoded.
# Future: read from user settings (e.g. config["CLASSIFIER_STRATEGY"])
_ACTIVE_STRATEGY = "llm"


def get_classifier() -> ClassifierStrategy:
    """Factory — returns the active classifier strategy."""
    return STRATEGIES[_ACTIVE_STRATEGY]()
