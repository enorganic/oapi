from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType

import pytest

from oapi.client import ClientModule
from oapi.model import ModelModule
from oapi.oas.model import OpenAPI


@pytest.fixture
def generated_module_loader(
    tmp_path: Path,
) -> Iterator[Callable[..., ModuleType]]:
    loaded_module_names: list[str] = []

    def load(source: str, module_name: str = "generated_module") -> ModuleType:
        module_path = tmp_path / f"{module_name}.py"
        module_path.write_text(source)
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            message = f"Unable to load a module from {module_path}"
            raise ImportError(message)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        loaded_module_names.append(module_name)
        spec.loader.exec_module(module)
        return module

    yield load
    for module_name in loaded_module_names:
        sys.modules.pop(module_name, None)


@pytest.fixture
def generated_client_package(
    tmp_path: Path,
) -> Iterator[Callable[[OpenAPI], tuple[ModuleType, ModuleType]]]:
    """
    Generates a real `oapi.model`/`oapi.client` module pair from a real
    `OpenAPI` document, writes them into a real, importable package (the
    generated client module uses a package-relative `from . import
    model` import, so it cannot be loaded as a standalone file the way
    `generated_module_loader` loads single files), and returns
    `(model_module, client_module)`.
    """
    loaded_module_names: list[str] = []
    inserted_sys_path: str | None = None

    def load(
        open_api: OpenAPI, package_name: str = "generated_client_pkg"
    ) -> tuple[ModuleType, ModuleType]:
        nonlocal inserted_sys_path
        package_dir: Path = tmp_path / package_name
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("")
        model_path: Path = package_dir / "model.py"
        model_path.write_text(str(ModelModule(open_api)))
        client_path: Path = package_dir / "client.py"
        ClientModule(open_api, model_path=str(model_path)).save(
            str(client_path)
        )
        if inserted_sys_path is None:
            sys.path.insert(0, str(tmp_path))
            inserted_sys_path = str(tmp_path)
        model_module: ModuleType = importlib.import_module(
            f"{package_name}.model"
        )
        client_module: ModuleType = importlib.import_module(
            f"{package_name}.client"
        )
        loaded_module_names.extend(
            (package_name, f"{package_name}.model", f"{package_name}.client")
        )
        return model_module, client_module

    yield load
    for module_name in loaded_module_names:
        sys.modules.pop(module_name, None)
    if inserted_sys_path is not None and inserted_sys_path in sys.path:
        sys.path.remove(inserted_sys_path)
