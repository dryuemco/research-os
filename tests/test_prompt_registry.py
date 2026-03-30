from pathlib import Path

import pytest

from app.services.prompt_registry_service import PromptNotFoundError, PromptRegistryService


def test_prompt_registry_loads_existing_prompt() -> None:
    service = PromptRegistryService(Path("prompts"))
    prompt = service.get_prompt("call_parser")
    assert "Call Parser" in prompt


def test_prompt_registry_raises_for_missing_prompt() -> None:
    service = PromptRegistryService(Path("prompts"))
    with pytest.raises(PromptNotFoundError):
        service.get_prompt("does_not_exist")
