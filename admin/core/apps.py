"""Django app config for admin.core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core application config."""

    name = "admin.core"
    verbose_name = "Core Domain"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Wire cache invalidation for the operator's settings layer.

        InfrastructureConfig holds deployment endpoints an administrator edits
        from the UI. The resolver holds those rows so the request path reads a
        dict instead of the ORM. An edit must take effect without a restart, so
        save/delete drop the cache.

        No query runs here. Django warns (and migrations break) when
        ``ready()`` touches the database; the cache is warmed at ASGI import
        time instead, which is still before the event loop serves anything.
        """
        from django.db.models.signals import post_delete, post_save

        from admin.core.helpers.service_urls import invalidate_infraconfig_cache
        from admin.core.infrastructure.models import InfrastructureConfig

        def _drop(*_args, **_kwargs) -> None:
            invalidate_infraconfig_cache()
            # The memory gateway binds SOMABRAIN_URL at construction. Dropping
            # the singleton here is what makes a UI edit of that URL repoint
            # the memory lane without a process restart (W2.1). The seam file
            # is untouched — this only clears its process-local cache.
            import services.common.memory_gateway as memory_gateway_mod

            memory_gateway_mod._memory_gateway_instance = None
            from admin.core import chat_orchestrator as co

            co._memory_gateway_cache = None
            co._memory_gateway_url = None

        post_save.connect(
            _drop, sender=InfrastructureConfig, dispatch_uid="soma_infra_cache_save"
        )
        post_delete.connect(
            _drop, sender=InfrastructureConfig, dispatch_uid="soma_infra_cache_delete"
        )
