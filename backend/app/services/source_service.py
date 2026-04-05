class SourceConfidenceService:
    def label_for_score(self, score: float) -> str:
        if score >= 0.9:
            return "high"
        if score >= 0.75:
            return "medium"
        return "low"

    def severity_for_score(self, score: float) -> str:
        if score >= 0.95:
            return "critical"
        if score >= 0.85:
            return "high"
        if score >= 0.7:
            return "medium"
        return "low"

    def summary_for_match(self, *, asset_title: str, matched_asset_title: str, score: float) -> str:
        label = self.label_for_score(score)
        percentage = round(score * 100, 1)
        return (
            f"Potential reuse detected for '{asset_title}' against "
            f"'{matched_asset_title}' with {percentage}% similarity ({label} confidence)."
        )

