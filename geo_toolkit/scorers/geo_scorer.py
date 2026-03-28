"""Calculate weighted GEO citability scores."""


class GEOScorer:
    """Calculate an overall GEO score from individual audit results."""

    def calculate(self, audit_results):
        """Calculate weighted average score and letter grade.

        Args:
            audit_results: List of audit result dicts with 'score' and 'weight' keys.

        Returns:
            Tuple of (score: int, grade: str)
        """
        total_weight = 0
        weighted_sum = 0

        for result in audit_results:
            weight = result.get("weight", 1)
            score = result.get("score", 0)
            weighted_sum += score * weight
            total_weight += weight

        overall = round(weighted_sum / total_weight) if total_weight > 0 else 0
        grade = self._score_to_grade(overall)

        return overall, grade

    def _score_to_grade(self, score):
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 40:
            return "D"
        return "F"
