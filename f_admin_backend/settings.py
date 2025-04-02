import os


class Settings:
    ADMIN_EXCLUDE_MODELS: list = os.environ.get('F_ADMIN_EXCLUDE_MODELS', [])


settings = Settings()

__all__ = ('settings',)
