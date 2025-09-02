from __future__ import annotations

import re
from itertools import chain
from pathlib import Path
from re import Match
from typing import TYPE_CHECKING, Any

import sob

from oapi.oas import model

if TYPE_CHECKING:
    from collections.abc import Iterable

PROJECT_PATH: Path = Path(__file__).absolute().parent.parent
MODEL_PATH: Path = PROJECT_PATH / "src" / "oapi" / "oas" / "model.py"


def get_region_source(name: str) -> str:
    with open(MODEL_PATH) as model_io:
        match: Match | None = re.search(
            (
                f"\\n#\\s*region\\s*{re.escape(name)}"
                r"(\n|.)*?"
                r"\n\s*#\s*endregion\s*\n"
            ),
            model_io.read(),
            flags=re.IGNORECASE,
        )
        return match.group().strip() if match else ""


def iter_source_names_models() -> Iterable[tuple[str, type[sob.abc.Model]]]:
    name: str
    value: Any
    for name in dir(model):
        value = getattr(model, name, None)
        if isinstance(value, type) and issubclass(value, sob.abc.Model):
            value.__module__ = "oapi.oas.model"
            yield name, value


def iter_names_metadata_docstrings_suffixes() -> (
    Iterable[tuple[str, sob.abc.Meta, str, str]]
):
    def get_name_metadata(
        item: tuple[str, type[sob.abc.Model]],
    ) -> tuple[str, sob.abc.Meta, str, str]:
        line: str
        meta: sob.abc.Meta | None = sob.read_model_meta(item[1])
        if not meta:
            raise ValueError(item[1])
        return (
            item[0],
            meta,
            "\n".join(
                line[4:] if line.startswith("    ") else line
                for line in (item[1].__doc__ or "").strip().split("\n")
            ),
            sob.utilities.get_source(item[1])
            .partition("super().__init__(_data)")[2]
            .strip(),
        )

    return map(get_name_metadata, iter_source_names_models())


def iter_models_metadata_suffixes() -> (
    Iterable[tuple[type[sob.abc.Model], sob.abc.Meta, str]]
):
    name: str
    suffix: str
    metadata: sob.abc.Meta
    for (
        name,
        metadata,
        docstring,
        suffix,
    ) in iter_names_metadata_docstrings_suffixes():
        if metadata:
            yield (
                sob.get_model_from_meta(
                    name,
                    metadata,
                    module="oapi.oas.model",
                    docstring=docstring.strip(),
                ),
                metadata,
                suffix,
            )


def main() -> None:
    suffix: str
    cls: type[sob.abc.Model]
    metadata: sob.abc.Meta
    imports: set[str] = {
        "from oapi._utilities import deprecated as _deprecated",
    }
    classes: list[str] = []
    metadatas: list[str] = []
    for cls, metadata, suffix in iter_models_metadata_suffixes():
        import_source: str
        class_source: str
        import_source, _, class_source = (
            sob.utilities.get_source(cls)
            .replace("oapi.oas.model.", "")
            .rpartition("\n\n\n")
        )
        if suffix:
            class_source = f"{class_source.rstrip()}\n        {suffix}"
        if import_source:
            imports |= set(import_source.strip().split("\n"))
        classes.append(class_source.strip())
        if not isinstance(
            metadata,
            (sob.abc.ObjectMeta, sob.abc.ArrayMeta, sob.abc.DictionaryMeta),
        ):
            raise TypeError(metadata)
        if isinstance(metadata, sob.abc.ObjectMeta):
            metadatas.append(
                re.sub(
                    r"\boapi\.oas\.model\.",
                    "",
                    sob.thesaurus.get_class_meta_attribute_assignment_source(
                        cls.__name__, "properties", metadata
                    ),
                )
            )
        elif isinstance(metadata, sob.abc.ArrayMeta):
            metadatas.append(
                re.sub(
                    r"\boapi\.oas\.model\.",
                    "",
                    sob.thesaurus.get_class_meta_attribute_assignment_source(
                        cls.__name__, "item_types", metadata
                    ),
                )
            )
        else:
            metadatas.append(
                re.sub(
                    r"\boapi\.oas\.model\.",
                    "",
                    sob.thesaurus.get_class_meta_attribute_assignment_source(
                        cls.__name__, "value_types", metadata
                    ),
                )
            )
    import_statement: str
    model_source: str = "\n\n".join(
        chain(
            (
                "\n".join(
                    chain(
                        (f'"""{model.__doc__.rstrip()}\n"""',),
                        sorted(
                            imports - {"import decimal"},
                            key=lambda import_statement: (
                                (0, import_statement)
                                if import_statement.startswith(
                                    "from __future__"
                                )
                                else (
                                    (2, import_statement)
                                    if import_statement.startswith("from ")
                                    else (1, import_statement)
                                )
                            ),
                        ),
                    )
                ),
            ),
            ("\nif typing.TYPE_CHECKING:\n    import decimal\n",),
            ("\n{}\n".format("\n\n\n".join(classes)),),
            ("\n".join(metadatas),),
            (get_region_source("Aliases"),),
            (get_region_source("Hooks"),),
        )
    )
    model_source = f"{model_source}\n"
    with open(MODEL_PATH, "w") as model_io:
        model_io.write(model_source)


if __name__ == "__main__":
    main()
