from rule_engine import evaluate


class RuleAgent:
    """Input: one structured measurement; output: rule results, issues and alerts."""

    def run(self, measurement: dict) -> dict:
        return evaluate(measurement)
