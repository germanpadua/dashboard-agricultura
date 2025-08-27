"""
Módulo de integraciones externas
Contiene clases y utilidades para integrar datos de fuentes externas como Telegram Bot
"""

from .telegram_sync import TelegramDataSync, telegram_sync

__all__ = ['TelegramDataSync', 'telegram_sync']
