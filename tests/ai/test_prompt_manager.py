"""Tests for PromptManager."""

from pathlib import Path

import pytest

from app.ai.prompt_manager import PromptManager
from app.exceptions import InvalidPromptError


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    """Create a temporary prompts directory with test templates."""
    base = tmp_path / "prompts"
    template_dir = base / "analysis" / "test-analysis" / "v1"
    template_dir.mkdir(parents=True)

    (template_dir / "system.md").write_text(
        "You are a {{ role }}.\n\nAnalyze the following:\n\n{{ artifact }}",
    )
    return base


@pytest.fixture
def prompts_dir_with_examples(tmp_path: Path) -> Path:
    """Create a prompts directory with both system.md and examples.md."""
    base = tmp_path / "prompts"
    template_dir = base / "analysis" / "test-analysis" / "v1"
    template_dir.mkdir(parents=True)

    (template_dir / "system.md").write_text(
        "You are a {{ role }}.\n\nFollow the output format.",
    )
    (template_dir / "examples.md").write_text(
        "## Example\nInput: X\nOutput: Y",
    )
    return base


@pytest.fixture
def prompt_manager(prompts_dir: Path) -> PromptManager:
    """PromptManager backed by temporary templates."""
    return PromptManager(prompts_dir)


@pytest.fixture
def prompt_manager_with_examples(prompts_dir_with_examples: Path) -> PromptManager:
    """PromptManager backed by templates with examples."""
    return PromptManager(prompts_dir_with_examples)


def test_load_renders_system_prompt(prompt_manager: PromptManager) -> None:
    """Template variables are interpolated correctly."""
    prompt = prompt_manager.load(
        analysis_type="test-analysis",
        context={"role": "QA engineer", "artifact": "Test requirement"},
    )
    assert "QA engineer" in prompt.system_prompt
    assert "Test requirement" in prompt.system_prompt


def test_load_with_examples(prompt_manager_with_examples: PromptManager) -> None:
    """Examples file content is included in user_message."""
    prompt = prompt_manager_with_examples.load(
        analysis_type="test-analysis",
        context={"role": "QA engineer", "artifact": "Req text"},
    )
    assert "Req text" in prompt.user_message
    assert "Example" in prompt.user_message


def test_load_without_examples(prompt_manager: PromptManager) -> None:
    """User message is just the artifact when no examples.md exists."""
    prompt = prompt_manager.load(
        analysis_type="test-analysis",
        context={"role": "QA engineer", "artifact": "Req text"},
    )
    assert prompt.user_message == "Req text"


def test_load_defaults_to_v1(prompt_manager: PromptManager) -> None:
    """Version defaults to 'v1'."""
    prompt = prompt_manager.load(
        analysis_type="test-analysis",
        context={"role": "R", "artifact": "A"},
    )
    assert prompt.metadata.version == "v1"


def test_load_metadata(prompt_manager: PromptManager) -> None:
    """TemplateMetadata contains analysis type and version."""
    prompt = prompt_manager.load(
        analysis_type="test-analysis",
        context={"role": "R", "artifact": "A"},
    )
    assert prompt.metadata.analysis_type == "test-analysis"
    assert prompt.metadata.version == "v1"


def test_load_missing_variable_raises(prompt_manager: PromptManager) -> None:
    """Missing template variables raise InvalidPromptError."""
    with pytest.raises(InvalidPromptError, match="Missing template variable"):
        prompt_manager.load(
            analysis_type="test-analysis",
            context={},  # missing "role" and "artifact"
        )


def test_load_missing_template_raises(prompt_manager: PromptManager) -> None:
    """Non-existent analysis type raises InvalidPromptError."""
    with pytest.raises(InvalidPromptError, match="Template not found"):
        prompt_manager.load(
            analysis_type="nonexistent",
            context={"role": "R", "artifact": "A"},
        )


def test_cache_hits(prompt_manager: PromptManager) -> None:
    """Repeated loads cache the template and still render correctly."""
    ctx = {"role": "QA", "artifact": "Test"}
    first = prompt_manager.load("test-analysis", ctx)
    second = prompt_manager.load("test-analysis", ctx)
    assert first.system_prompt == second.system_prompt
    assert first.user_message == second.user_message


def test_clear_cache(prompt_manager: PromptManager) -> None:
    """Clear cache forces re-read from filesystem."""
    prompt_manager.load(
        "test-analysis",
        {"role": "R", "artifact": "A"},
    )
    prompt_manager.clear_cache()
    # Should still work after cache clear
    prompt = prompt_manager.load(
        "test-analysis",
        {"role": "R", "artifact": "A"},
    )
    assert "R" in prompt.system_prompt


def test_init_nonexistent_dir_raises() -> None:
    """PromptManager raises InvalidPromptError for non-existent directory."""
    with pytest.raises(InvalidPromptError, match="does not exist"):
        PromptManager("/nonexistent/path")


def test_different_versions(prompts_dir: Path) -> None:
    """Different versions load different templates."""
    # Create a v2 template
    v2_dir = prompts_dir / "analysis" / "test-analysis" / "v2"
    v2_dir.mkdir(parents=True)
    (v2_dir / "system.md").write_text(
        "You are a {{ role }} in v2.\n\n{{ artifact }}",
    )

    pm = PromptManager(prompts_dir)
    v1 = pm.load("test-analysis", {"role": "R", "artifact": "A"}, version="v1")
    v2 = pm.load("test-analysis", {"role": "R", "artifact": "A"}, version="v2")

    assert "v2" in v2.system_prompt
    assert "v2" not in v1.system_prompt
