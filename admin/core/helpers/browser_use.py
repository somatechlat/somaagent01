"""Module browser_use."""

from admin.core.helpers import dotenv

dotenv.save_dotenv_value("ANONYMIZED_TELEMETRY", "false")