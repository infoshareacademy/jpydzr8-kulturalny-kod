from decimal import Decimal
from typing import Any, Dict
from django.http import HttpRequest

from .base import BaseProvider, CreateSessionResult, WebhookResult


class DummyProvider(BaseProvider):
    name = "dummy"

    def create_session(
        self,
        *,
        amount: Decimal,
        currency: str,
        description: str,
        metadata: Dict[str, Any],
    ) -> CreateSessionResult:
        return CreateSessionResult(
            ok=True,
            external_id="dummy-session-123",
            redirect_url=None,
            raw={
                "note": "dummy session",
                "amount": str(amount),
                "currency": currency,
                "description": description,
                "metadata": metadata,
            },
        )

    def verify_webhook(self, request: HttpRequest) -> WebhookResult:
        return {
            "ok": True,
            "external_id": "dummy-session-123",
            "status": "succeeded",
            "raw": {"info": "simulated webhook"},
        }
