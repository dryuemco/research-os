from pathlib import Path


class PromptNotFoundError(FileNotFoundError):
    pass


class PromptRegistryService:
    def __init__(self, prompt_root: Path) -> None:
        self.prompt_root = prompt_root

    def get_prompt(self, prompt_key: str, *, version: str | None = None) -> str:
        if version:
            path = self.prompt_root / f"{prompt_key}.{version}.md"
            if path.exists():
                return path.read_text()

        default_path = self.prompt_root / f"{prompt_key}.md"
        if default_path.exists():
            return default_path.read_text()

        raise PromptNotFoundError(f"Prompt '{prompt_key}' not found under {self.prompt_root}")
