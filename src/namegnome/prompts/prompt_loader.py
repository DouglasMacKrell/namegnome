"""Prompt template loader for NameGnome.

Loads and renders Jinja2 templates from the prompts directory.
"""

from pathlib import Path

import jinja2

PROMPTS_DIR = Path(__file__).parent  # Can be monkeypatched in tests


def render_prompt(template_name: str, **context: object) -> str:
    """Render a Jinja2 template from the prompts directory with the given context.

    Args:
        template_name: The filename of the template (e.g., 'foo.j2').
        **context: Variables to pass to the template.

    Returns:
        The rendered template as a string.

    Raises:
        jinja2.exceptions.TemplateNotFound: If the template does not exist.
        jinja2.exceptions.UndefinedError: If a required variable is missing.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(PROMPTS_DIR)),
        undefined=jinja2.StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return str(template.render(**context))
