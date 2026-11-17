from odoo.modules.registry import Registry

# Odoo 20 moved ormcache invalidation to Transaction.invalidate_ormcache,
# dropping Registry.clear_cache. Provide a compatibility shim so callers
# (and test fixtures) targeting both series continue to invalidate caches cleanly.
if not hasattr(Registry, "clear_cache"):
    def _compat_registry_clear_cache(self, *cache_names: str) -> None:
        for _seq, cache in getattr(self, "registry_caches__", {}).values():
            try:
                cache.clear()
            except Exception:
                pass
        try:
            from odoo.http import request

            if request and getattr(request, "env", None):
                for name in cache_names or ("default",):
                    request.env.transaction.invalidate_ormcache(name)
        except Exception:
            pass

    Registry.clear_cache = _compat_registry_clear_cache

from . import controllers
from . import models
from . import wizard
