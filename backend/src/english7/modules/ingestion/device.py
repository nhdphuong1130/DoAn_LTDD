from collections.abc import Callable
from enum import StrEnum


class InferenceDevice(StrEnum):
    CPU = "cpu"
    CUDA = "cuda"

    @property
    def doclayout_value(self) -> str:
        return "0" if self is InferenceDevice.CUDA else "cpu"

    @property
    def paddle_value(self) -> str:
        return "gpu:0" if self is InferenceDevice.CUDA else "cpu"


def resolve_device(
    requested: str, *, cuda_available: Callable[[], bool]
) -> InferenceDevice:
    normalized = requested.strip().lower()
    if normalized not in {"auto", "cpu", "cuda"}:
        raise ValueError("Inference device must be auto, cpu, or cuda")
    available = cuda_available()
    if normalized == "cuda" and not available:
        raise RuntimeError("CUDA was requested but is not available")
    if normalized == "cuda" or (normalized == "auto" and available):
        return InferenceDevice.CUDA
    return InferenceDevice.CPU


def torch_cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())
