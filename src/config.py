"""
Centralized configuration for AI models and providers.
"""
import os
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelConfig:
    """Configuration for AI model selection and API keys."""

    # Default provider
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()

    # Model names for each provider
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

    # Main agent model (for LangChain orchestration)
    MAIN_AGENT_MODEL = os.getenv("MAIN_AGENT_MODEL", "gpt-4o-mini")

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    # Optional settings
    VERBOSE_BROWSER_LOGS = os.getenv("VERBOSE_BROWSER_LOGS", "false").lower() == "true"
    ENABLE_PROPERTY_CACHE = os.getenv("ENABLE_PROPERTY_CACHE", "true").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    @classmethod
    def get_llm(cls, provider: str = None, model: str = None) -> Any:
        """
        Get the appropriate LLM instance based on provider.

        Args:
            provider: AI provider (openai, anthropic, google). If None, uses AI_PROVIDER from env.
            model: Specific model name. If None, uses the default for the provider.

        Returns:
            LLM instance configured for the specified provider

        Raises:
            ValueError: If provider is not supported or API key is missing
        """
        provider = (provider or cls.AI_PROVIDER).lower()

        if provider == "openai":
            from langchain_openai import ChatOpenAI

            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            model_name = model or cls.OPENAI_MODEL
            return ChatOpenAI(
                model=model_name,
                api_key=cls.OPENAI_API_KEY,
                temperature=0.1  # Low temperature for consistent results
            )

        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            if not cls.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

            model_name = model or cls.ANTHROPIC_MODEL
            return ChatAnthropic(
                model=model_name,
                api_key=cls.ANTHROPIC_API_KEY,
                temperature=0.1
            )

        elif provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            api_key = cls.GOOGLE_API_KEY or cls.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")

            model_name = model or cls.GOOGLE_MODEL

            # Set both environment variables for compatibility
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ["GEMINI_API_KEY"] = api_key

            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.1
            )

        else:
            raise ValueError(
                f"Unsupported AI provider: {provider}. "
                f"Supported providers: openai, anthropic, google"
            )

    @classmethod
    def get_browser_llm(cls) -> Any:
        """
        Get the LLM instance for browser automation.
        Uses the configured AI_PROVIDER and corresponding model.

        Returns:
            LLM instance for browser automation
        """
        return cls.get_llm(provider=cls.AI_PROVIDER)

    @classmethod
    def get_main_agent_llm(cls) -> Any:
        """
        Get the LLM instance for the main LangChain agent.

        Returns:
            LLM instance for main agent
        """
        # Determine provider from model name
        model = cls.MAIN_AGENT_MODEL

        if "gpt" in model or "openai" in model:
            return cls.get_llm(provider="openai", model=model)
        elif "claude" in model or "anthropic" in model:
            return cls.get_llm(provider="anthropic", model=model)
        elif "gemini" in model or "google" in model:
            return cls.get_llm(provider="google", model=model)
        else:
            # Default to configured provider
            return cls.get_llm(provider=cls.AI_PROVIDER, model=model)

    @classmethod
    def get_model_info(cls) -> dict:
        """
        Get current model configuration info.

        Returns:
            Dictionary with current model settings
        """
        return {
            "provider": cls.AI_PROVIDER,
            "browser_model": {
                "openai": cls.OPENAI_MODEL,
                "anthropic": cls.ANTHROPIC_MODEL,
                "google": cls.GOOGLE_MODEL,
            }.get(cls.AI_PROVIDER, "unknown"),
            "main_agent_model": cls.MAIN_AGENT_MODEL,
            "cache_enabled": cls.ENABLE_PROPERTY_CACHE,
            "cache_ttl": cls.CACHE_TTL_SECONDS,
            "verbose_logs": cls.VERBOSE_BROWSER_LOGS,
        }


# Convenience function
def get_llm(provider: str = None, model: str = None):
    """Convenience function to get LLM instance."""
    return ModelConfig.get_llm(provider, model)
