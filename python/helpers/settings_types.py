"""Settings type definitions.

This module contains TypedDict definitions for settings UI representation.
Extracted from settings.py for better modularity.
"""

from typing import Any, Literal, TypedDict


class FieldOption(TypedDict):
    """Option for select/dropdown fields."""
    value: str
    label: str


class SettingsField(TypedDict, total=False):
    """Definition of a single settings field for UI rendering."""
    id: str
    title: str
    description: str
    type: Literal[
        "text",
        "number",
        "select",
        "range",
        "textarea",
        "password",
        "switch",
        "button",
        "html",
    ]
    value: Any
    min: float
    max: float
    step: float
    hidden: bool
    options: list[FieldOption]
    style: str


class SettingsSection(TypedDict, total=False):
    """Definition of a settings section containing multiple fields."""
    id: str
    title: str
    description: str
    fields: list[SettingsField]
    tab: str  # Indicates which tab this section belongs to


class SettingsOutput(TypedDict):
    """Output structure for settings UI."""
    sections: list[SettingsSection]


# Placeholder constants for sensitive values
PASSWORD_PLACEHOLDER = "****PSWD****"
API_KEY_PLACEHOLDER = "************"
