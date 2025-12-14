import json
import logging
from pathlib import Path
from typing import Optional

from macrolens_poc.config import Settings
from macrolens_poc.llm.provider import LLMProvider
from macrolens_poc.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, settings: Settings, provider: Optional[LLMProvider] = None):
        self.settings = settings
        # If no provider injected, default to OpenAIProvider using settings
        if provider is None:
            self.provider = OpenAIProvider(settings.llm)
        else:
            self.provider = provider

    def analyze_report(self, report_path: Path) -> str:
        """
        Loads a JSON report, renders prompts, and requests analysis from the LLM.
        Returns the analysis as a Markdown string.
        """
        if not report_path.exists():
            raise FileNotFoundError(f"Report file not found: {report_path}")

        # 1. Load Report Data
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            # Convert back to string for injection (pretty printed for better LLM readability)
            report_json_str = json.dumps(report_data, indent=2)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in report file: {e}")

        # 2. Load Prompts
        prompts_dir = Path(__file__).parent / "prompts"
        system_prompt_path = prompts_dir / "system.md"
        user_prompt_path = prompts_dir / "user.md"

        if not system_prompt_path.exists() or not user_prompt_path.exists():
             raise FileNotFoundError("Prompt templates (system.md/user.md) missing in package.")

        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        user_prompt_template = user_prompt_path.read_text(encoding="utf-8")

        # 3. Inject Data
        # Simple string replacement for PoC
        user_prompt = user_prompt_template.replace("{{ report_json }}", report_json_str)

        # 4. Call Provider
        logger.info(f"Requesting analysis for report: {report_path.name} using model {self.settings.llm.model}")
        analysis_md = self.provider.generate_analysis(system_prompt, user_prompt)
        
        return analysis_md