"""Template string utilities for rendering t-strings.

This module provides utilities for converting Python 3.14 template strings
(t-strings) to regular strings with proper formatting and conversion support.
"""

from string.templatelib import Interpolation, Template


def convert(value: object, conversion: str | None) -> object:
    """Apply conversion flags to a value.

    Args:
        value: The value to convert
        conversion: Conversion flag ('s', 'r', or 'a')

    Returns:
        Converted value
    """
    if conversion == "a":
        return ascii(value)
    if conversion == "r":
        return repr(value)
    if conversion == "s":
        return str(value)
    return value


def render_template(template: Template) -> str:
    """Convert a Template object to a string.

    This function processes a Template object created by a t-string literal
    and converts it to a regular string, applying conversion and format
    specifications similar to f-strings.

    Args:
        template: Template object created by a t-string literal

    Returns:
        Rendered string

    Example:
        >>> name = "World"
        >>> template = t"Hello {name}!"
        >>> render_template(template)
        'Hello World!'
    """
    parts = []
    for item in template:
        match item:
            case str() as s:
                # Static string part
                parts.append(s)
            case Interpolation(value, _, conversion, format_spec):
                # Apply conversion flags (!s, !r, !a)
                value = convert(value, conversion)
                # Apply format specification
                value = format(value, format_spec or "")
                parts.append(str(value))
    return "".join(parts)
