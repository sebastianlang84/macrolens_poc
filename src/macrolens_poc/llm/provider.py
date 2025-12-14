from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_analysis(self, system_prompt: str, user_prompt: str) -> str:
        """
        Sendet Prompts an das LLM und gibt die Antwort als String zurück.
        Sollte Retries und Error-Handling beinhalten.
        """
        pass