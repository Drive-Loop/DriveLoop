__all__ = ["LongTailScenarioController", "MultimodalConditioner", "PromptConditioningResult", "MicrophoneRecorder"]


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
    if name == "MicrophoneRecorder":
        from driveloop.conditioning.audio import MicrophoneRecorder

        return MicrophoneRecorder
    raise AttributeError(f"module 'driveloop.conditioning' has no attribute {name}")
