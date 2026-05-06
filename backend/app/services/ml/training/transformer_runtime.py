from __future__ import annotations

import importlib.machinery
import sys
import types


def ensure_text_only_transformers_runtime() -> None:
    try:
        import torchvision  # noqa: F401
        return
    except Exception:
        pass

    torchvision_stub = types.ModuleType("torchvision")
    torchvision_stub.__spec__ = importlib.machinery.ModuleSpec("torchvision", loader=None)

    transforms_stub = types.ModuleType("torchvision.transforms")
    transforms_stub.__spec__ = importlib.machinery.ModuleSpec("torchvision.transforms", loader=None)
    transforms_stub.__path__ = []

    functional_stub = types.ModuleType("torchvision.transforms.functional")
    functional_stub.__spec__ = importlib.machinery.ModuleSpec("torchvision.transforms.functional", loader=None)

    class InterpolationMode:
        NEAREST = 0
        NEAREST_EXACT = 0
        BILINEAR = 1
        BICUBIC = 2
        LANCZOS = 3
        HAMMING = 4
        BOX = 5

    transforms_stub.InterpolationMode = InterpolationMode
    functional_stub.pil_to_tensor = lambda *args, **kwargs: None
    torchvision_stub.transforms = transforms_stub

    for name in [
        "_meta_registrations",
        "datasets",
        "io",
        "models",
        "ops",
        "utils",
    ]:
        module_name = f"torchvision.{name}"
        submodule = types.ModuleType(module_name)
        submodule.__spec__ = importlib.machinery.ModuleSpec(module_name, loader=None)
        if name == "io":
            class ImageReadMode:
                UNCHANGED = 0
                GRAY = 1
                GRAY_ALPHA = 2
                RGB = 3
                RGB_ALPHA = 4

            submodule.ImageReadMode = ImageReadMode
            submodule.decode_image = lambda *args, **kwargs: None
            submodule.read_file = lambda *args, **kwargs: None
        sys.modules.setdefault(module_name, submodule)
        setattr(torchvision_stub, name, submodule)

    sys.modules["torchvision"] = torchvision_stub
    sys.modules["torchvision.transforms"] = transforms_stub
    sys.modules["torchvision.transforms.functional"] = functional_stub
