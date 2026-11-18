"""Простой DI-контейнер: фабрики, разрешение и scoped override."""

from contextlib import contextmanager


class Container:
    def __init__(self):
        self.providers = {}
        self.resolving = set()

    def register(self, key, factory):
        self.providers[key] = factory

    def resolve(self, key):
        if key not in self.providers:
            raise LookupError(f"Зависимость не зарегистрирована: {key}")
        if key in self.resolving:
            raise RuntimeError(f"Циклическая зависимость: {key}")
        self.resolving.add(key)
        try:
            return self.providers[key](self)
        finally:
            self.resolving.remove(key)

    @contextmanager
    def override(self, key, factory):
        missing = object()
        previous = self.providers.get(key, missing)
        self.register(key, factory)
        try:
            yield self
        finally:
            if previous is missing:
                self.providers.pop(key)
            else:
                self.providers[key] = previous
