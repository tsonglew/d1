"""Chat model helpers for the desktop pet."""

from .factory import ChatModelSettings, create_chat_model
from .local import LocalPetChatModel

__all__ = ["ChatModelSettings", "LocalPetChatModel", "create_chat_model"]

