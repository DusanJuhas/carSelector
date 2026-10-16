from typing import Literal

from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Body of `GET /healthz` - only ever "ok": a process that can answer at
    all is alive, and anything worse shows up as no answer or a 5xx.
    """

    status: Literal["ok"] = "ok"
