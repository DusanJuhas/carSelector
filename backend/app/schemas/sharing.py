from datetime import datetime

from pydantic import BaseModel

from app.schemas.vehicle import VehicleSummary


class SharedRequirement(BaseModel):
    """One requirement line on a shared page - `UserRequirement` without
    its `source` (the user's own chat words, which may say more about them
    than they meant to share) and `changed` (UI flash state)."""

    label: str
    value: str


class SharedSnapshotContent(BaseModel):
    """What a shared link shows - stored as `shared_snapshots.content_json`."""

    requirements: list[SharedRequirement]
    vehicles: list[VehicleSummary]


class SharedSnapshot(BaseModel):
    """A loaded, still-valid shared snapshot."""

    token: str
    content: SharedSnapshotContent
    created_at: datetime
    expires_at: datetime
