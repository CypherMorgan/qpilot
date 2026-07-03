"""Prompt Manager.

Loads, caches, and renders prompt templates from the filesystem.
Templates are versioned Markdown files using Jinja2 for variable
interpolation.

No prompt strings exist in Python source code — all prompts live in
``prompts/`` as versioned files tracked in git.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

from app.exceptions import InvalidPromptError


class TemplateMetadata:
    """Version and provenance information for a rendered prompt template."""

    def __init__(
        self,
        analysis_type: str,
        version: str,
        template_path: Path,
    ) -> None:
        self.analysis_type = analysis_type
        self.version = version
        self.template_path = template_path


class PromptTemplate:
    """A loaded and rendered prompt, ready to send to an AI provider."""

    def __init__(
        self,
        system_prompt: str,
        user_message: str,
        metadata: TemplateMetadata,
    ) -> None:
        self.system_prompt = system_prompt
        self.user_message = user_message
        self.metadata = metadata


class PromptManager:
    """Loads, caches, and renders prompt templates from the filesystem.

    Templates are stored under ``{prompts_dir}/analysis/{analysis_type}/{version}/``.
    Each template directory must contain at least ``system.md``.
    An optional ``examples.md`` file is appended to the user message.

    Usage::

        pm = PromptManager("./prompts")
        prompt = pm.load(
            analysis_type="requirement-analysis",
            context={"artifact": "...", "output_schema": "..."},
            version="v1",
        )
        # prompt.system_prompt  → rendered system instructions
        # prompt.user_message   → rendered user message + examples
    """

    def __init__(self, prompts_dir: str | Path) -> None:
        """Initialise the PromptManager.

        Args:
            prompts_dir: Root directory containing prompt templates.
                This should be the ``prompts/`` folder at the project root.
        """
        self._prompts_dir = Path(prompts_dir)
        if not self._prompts_dir.is_dir():
            raise InvalidPromptError(
                f"Prompts directory does not exist: {self._prompts_dir}",
            )

        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self._prompts_dir)),
            undefined=jinja2.StrictUndefined,
            autoescape=False,
        )
        self._cache: dict[str, jinja2.Template] = {}

    def load(
        self,
        analysis_type: str,
        context: dict[str, Any],
        version: str = "v1",
    ) -> PromptTemplate:
        """Load and render a prompt template for the given analysis type.

        Args:
            analysis_type: Analysis type identifier.
                This maps to a subdirectory under ``prompts/analysis/``.
            context: Template variables for Jinja2 interpolation.
            version: Template version directory (default ``"v1"``).

        Returns:
            A fully rendered ``PromptTemplate`` with system prompt and user message.

        Raises:
            InvalidPromptError: If the template directory or ``system.md``
                is missing, or if a required template variable is not provided.
        """
        template_base = f"analysis/{analysis_type}/{version}"

        system_prompt = self._render(f"{template_base}/system.md", context)

        examples_path = f"{template_base}/examples.md"
        examples_path_full = self._prompts_dir / examples_path
        if examples_path_full.exists():
            examples = self._render(examples_path, context)
            user_message = f"{context.get('artifact', '')}\n\n{examples}"
        else:
            user_message = context.get("artifact", "")

        return PromptTemplate(
            system_prompt=system_prompt,
            user_message=user_message,
            metadata=TemplateMetadata(
                analysis_type=analysis_type,
                version=version,
                template_path=self._prompts_dir / template_base,
            ),
        )

    def _render(self, template_path: str, context: dict[str, Any]) -> str:
        """Load (from cache or filesystem) and render a template.

        Args:
            template_path: Path relative to ``prompts_dir``.
            context: Template variables.

        Returns:
            Rendered template string.
        """
        if template_path not in self._cache:
            try:
                template = self._env.get_template(template_path)
            except jinja2.TemplateNotFound as exc:
                raise InvalidPromptError(
                    f"Template not found: {template_path}",
                    detail={"template_path": template_path},
                ) from exc
            self._cache[template_path] = template
        else:
            template = self._cache[template_path]

        try:
            return template.render(**context)
        except jinja2.UndefinedError as exc:
            raise InvalidPromptError(
                f"Missing template variable in {template_path}: {exc}",
                detail={"template_path": template_path, "error": str(exc)},
            ) from exc

    def clear_cache(self) -> None:
        """Clear the template cache.

        Useful when templates are edited at runtime (dev with volume mount).
        """
        self._cache.clear()
