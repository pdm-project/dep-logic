from dep_logic.tags import EnvSpec


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
