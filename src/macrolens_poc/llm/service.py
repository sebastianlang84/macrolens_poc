import json
import logging
from pathlib import Path
from typing import Optional

from macrolens_poc.config import Settings
from macrolens_poc.llm.openai_provider import OpenAIProvider
from macrolens_poc.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, settings: Settings, provider: Optional[LLMProvider] = None):
        self.settings = settings
        # If no provider injected, default to OpenAIProvider using settings
        if provider is None:
            self.provider = OpenAIProvider(settings.llm)
        else:
            self.provider = provider

    def analyze_report(self, report_path: Path, override_models: Optional[list[str]] = None) -> str:
        """
        Loads a JSON report, renders prompts, and requests analysis from the LLM(s).
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
            raise ValueError(f"Invalid JSON in report file: {e}") from e

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

        # 4. Call Provider for each model
        models = override_models if override_models else self.settings.llm.models
        results = []

        for model in models:
            logger.info(f"Requesting analysis for report: {report_path.name} using model {model}")
            try:
                analysis = self.provider.generate_analysis(system_prompt, user_prompt, model=model)
                results.append(f"## Analysis ({model})\n\n{analysis}")
            except Exception as e:
                logger.error(f"Analysis failed for model {model}: {e}")
                results.append(f"## Analysis ({model})\n\n*Analysis failed: {e}*")

        if not results:
            return "*No analysis generated (no models configured or all failed).*"

        return "\n\n---\n\n".join(results)
