from app.models.asset import Asset, AssetMatch
from app.models.user import APIKey, Organisation, User
from app.models.violation import EnforcementRecord, Violation


def load_all_models() -> None:
    _ = (
        Asset,
        AssetMatch,
        APIKey,
        Organisation,
        User,
        EnforcementRecord,
        Violation,
    )

