from django.apps import AppConfig


class FilesConfig(AppConfig):
    """Django app config for files."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.files"
    label = "admin_files"
    verbose_name = "File Management"
