import pytest

from dep_logic.tags import EnvSpec
from dep_logic.tags.tags import EnvCompatibility


def test_check_wheel_tags():
    wheels = [
        "protobuf-5.27.2-cp310-abi3-win32.whl",
        "protobuf-5.27.2-cp310-abi3-win_amd64.whl",
        "protobuf-5.27.2-cp310-cp310-macosx_12_0_arm64.whl",
        "protobuf-5.27.2-cp38-abi3-macosx_10_9_universal2.whl",
        "protobuf-5.27.2-cp38-abi3-manylinux2014_aarch64.whl",
        "protobuf-5.27.2-cp38-abi3-manylinux2014_x86_64.whl",
        "protobuf-5.27.2-cp38-cp38-win32.whl",
        "protobuf-5.27.2-cp38-cp38-win_amd64.whl",
        "protobuf-5.27.2-cp39-cp39-win32.whl",
        "protobuf-5.27.2-cp39-cp39-win_amd64.whl",
        "protobuf-5.27.2-py3-none-any.whl",
    ]

    linux_env = EnvSpec.from_spec(">=3.9", "linux", "cpython")
    wheel_compats = {
        f: c
        for f, c in {f: linux_env.wheel_compatibility(f) for f in wheels}.items()
        if c is not None
    }
    filtered_wheels = sorted(wheel_compats, key=wheel_compats.__getitem__, reverse=True)
    assert filtered_wheels == [
        "protobuf-5.27.2-cp38-abi3-manylinux2014_x86_64.whl",
        "protobuf-5.27.2-py3-none-any.whl",
    ]

    windows_env = EnvSpec.from_spec(">=3.9", "windows", "cpython")
    wheel_compats = {
        f: c
        for f, c in {f: windows_env.wheel_compatibility(f) for f in wheels}.items()
        if c is not None
    }
    filtered_wheels = sorted(wheel_compats, key=wheel_compats.__getitem__, reverse=True)
    assert filtered_wheels == [
        "protobuf-5.27.2-cp310-abi3-win_amd64.whl",
        "protobuf-5.27.2-cp39-cp39-win_amd64.whl",
        "protobuf-5.27.2-py3-none-any.whl",
    ]

    macos_env = EnvSpec.from_spec(">=3.9", "macos", "cpython")
    wheel_compats = {
        f: c
        for f, c in {f: macos_env.wheel_compatibility(f) for f in wheels}.items()
        if c is not None
    }
    filtered_wheels = sorted(wheel_compats, key=wheel_compats.__getitem__, reverse=True)
    assert filtered_wheels == [
        "protobuf-5.27.2-cp310-cp310-macosx_12_0_arm64.whl",
        "protobuf-5.27.2-cp38-abi3-macosx_10_9_universal2.whl",
        "protobuf-5.27.2-py3-none-any.whl",
    ]

    python_env = EnvSpec.from_spec(">=3.9")
    wheel_compats = {
        f: c
        for f, c in {f: python_env.wheel_compatibility(f) for f in wheels}.items()
        if c is not None
    }
    filtered_wheels = sorted(wheel_compats, key=wheel_compats.__getitem__, reverse=True)
    assert filtered_wheels == [
        "protobuf-5.27.2-cp310-cp310-macosx_12_0_arm64.whl",
        "protobuf-5.27.2-cp310-abi3-win32.whl",
        "protobuf-5.27.2-cp310-abi3-win_amd64.whl",
        "protobuf-5.27.2-cp39-cp39-win32.whl",
        "protobuf-5.27.2-cp39-cp39-win_amd64.whl",
        "protobuf-5.27.2-cp38-abi3-macosx_10_9_universal2.whl",
        "protobuf-5.27.2-cp38-abi3-manylinux2014_aarch64.whl",
        "protobuf-5.27.2-cp38-abi3-manylinux2014_x86_64.whl",
        "protobuf-5.27.2-py3-none-any.whl",
    ]


@pytest.mark.parametrize(
    "left,right,expected",
    [
        (
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvCompatibility.LOWER_OR_EQUAL,
        ),
        (
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvSpec.from_spec(">=3.9", "macos"),
            EnvCompatibility.LOWER_OR_EQUAL,
        ),
        (
            EnvSpec.from_spec(">=3.9", "macos"),
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvCompatibility.LOWER_OR_EQUAL,
        ),
        (
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvSpec.from_spec(">=3.7,<3.10"),
            EnvCompatibility.LOWER_OR_EQUAL,
        ),
        (
            EnvSpec.from_spec(">=3.7,<3.10"),
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvCompatibility.LOWER_OR_EQUAL,
        ),
        (
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvSpec.from_spec("<3.8", "macos", "cpython"),
            EnvCompatibility.INCOMPATIBLE,
        ),
        (
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvSpec.from_spec("<3.10", "linux", "cpython"),
            EnvCompatibility.INCOMPATIBLE,
        ),
        (
            EnvSpec.from_spec(">=3.9", "macos", "cpython"),
            EnvSpec.from_spec("<3.10", "macos", "pypy"),
            EnvCompatibility.INCOMPATIBLE,
        ),
        (
            EnvSpec.from_spec(">=3.9", "macos_x86_64", "cpython"),
            EnvSpec.from_spec("<3.10", "macos_10_9_x86_64", "cpython"),
            EnvCompatibility.HIGHER,
        ),
        (
            EnvSpec.from_spec("<3.10", "macos_10_9_x86_64", "cpython"),
            EnvSpec.from_spec(">=3.9", "macos_x86_64", "cpython"),
            EnvCompatibility.LOWER_OR_EQUAL,
        ),
    ],
)
def test_env_spec_comparison(left, right, expected):
    assert left.compare(right) == expected
