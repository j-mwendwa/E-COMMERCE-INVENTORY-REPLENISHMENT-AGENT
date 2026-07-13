
from src.config import ROOT_DIR

PROMPTS_DIR = ROOT_DIR / "prompts"


def load_prompt(name: str, version: str = "v1") -> str:
    path = PROMPTS_DIR / name / f"{version}.md"
    if not path.exists():
        path = PROMPTS_DIR / f"{name}_{version}.md"
    if not path.exists():
        msg = f"Prompt not found: {name}/{version} (tried {path})"
        raise FileNotFoundError(msg)
    return path.read_text().strip()


def load_prompt_from_config(name: str) -> str:
    from src.config import cfg
    prompts_cfg = cfg.get("prompts", {})
    version = prompts_cfg.get("version", "v1")
    return load_prompt(name, version)
