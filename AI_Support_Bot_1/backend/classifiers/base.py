from abc import ABC, abstractmethod


class ClassifierStrategy(ABC):
    """Contract all classifier strategies must follow."""

    @abstractmethod
    def classify(self, user_input: str) -> str:
        """Classify a user query.

        Returns:
            "simple"  — cheap/fast model is sufficient
            "complex" — capable model required
        """
