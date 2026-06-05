__all__ = ["LongTailScenarioController", "MultimodalConditioner", "PromptConditioningResult"]


def __getattr__(name):
    if name == "LongTailScenarioController":
        from driveloop.conditioning.long_tail import LongTailScenarioController

        return LongTailScenarioController
    if name in {"MultimodalConditioner", "PromptConditioningResult"}:
        from driveloop.conditioning.multimodal import MultimodalConditioner, PromptConditioningResult

        mapping = {
            "MultimodalConditioner": MultimodalConditioner,
            "PromptConditioningResult": PromptConditioningResult,
        }
        return mapping[name]
    raise AttributeError(f"module 'driveloop.conditioning' has no attribute {name}")
