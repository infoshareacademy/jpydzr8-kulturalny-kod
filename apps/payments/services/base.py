from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional, TypedDict
from abc import ABC, abstractmethod

from django.http import HttpRequest


class WebhookResult(TypedDict, total=False):
    ok: bool
    external_id: str
    status: str
    raw: Dict[str, Any]


@dataclass(frozen=True)
class CreateSessionResult:
    ok: bool
    external_id: Optional[str] = None
    redirect_url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def create_session(
        self,
        *,
        amount: Decimal,
        currency: str,
        description: str,
        metadata: Dict[str, Any],
    ) -> CreateSessionResult:
        raise NotImplementedError

    @abstractmethod
    def verify_webhook(self, request: HttpRequest) -> WebhookResult:
        raise NotImplementedError
