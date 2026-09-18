import pytest

from english7.modules.ingestion.device import InferenceDevice, resolve_device


def test_auto_uses_cuda_when_available() -> None:
    device = resolve_device("auto", cuda_available=lambda: True)

    assert device is InferenceDevice.CUDA
    assert device.doclayout_value == "0"
    assert device.paddle_value == "gpu:0"


def test_auto_falls_back_to_cpu() -> None:
    assert (
        resolve_device("auto", cuda_available=lambda: False)
        is InferenceDevice.CPU
    )


def test_explicit_cuda_fails_when_unavailable() -> None:
    with pytest.raises(RuntimeError, match="CUDA"):
        resolve_device("cuda", cuda_available=lambda: False)
