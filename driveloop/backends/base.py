from __future__ import annotations

from abc import ABC, abstractmethod

from driveloop.schema import DriveLoopRequest, Generation


class GenerationBackend(ABC):
    """Interface for fixed video generation backends such as DriveDreamer-2."""

    @abstractmethod
    def generate(self, request: DriveLoopRequest, iteration: int) -> Generation:
        raise NotImplementedError
