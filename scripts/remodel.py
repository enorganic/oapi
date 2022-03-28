from itertools import chain
import os
import re
import sob
from typing import Any, Iterable, List, Match, Optional, Set, Tuple, Type
from oapi.oas import model

PROJECT_PATH: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH: str = os.path.join(PROJECT_PATH, "oapi", "oas", "model.py")
EXTENSIBLE_MODEL_SOURCE: str = """
class ExtensibleObject(sob.model.Object):
    pass
""".strip()


def get_region_source(name: str) -> str:
    with open(MODEL_PATH) as model_io:
        match: Optional[Match] = re.search(
            (
                f"\\n#\\s*region\\s*{re.escape(name)}"
                r"(\n|.)*?"
                r"\n\s*#\s*endregion\s*\n"
            ),
            model_io.read(),
            flags=re.IGNORECASE,
        )
        return match.group().strip() if match else ""


def iter_source_names_models() -> Iterable[Tuple[str, Type[sob.abc.Model]]]:
    name: str
    value: Any
    for name in dir(model):
        value = getattr(model, name, None)
        if isinstance(value, type) and issubclass(value, sob.abc.Model):
            value.__module__ = "oapi.oas.model"
            yield name, value


def iter_names_metadata_docstrings_suffixes() -> Iterable[
    Tuple[str, sob.abc.Meta, str, str]
]:
    def get_name_metadata(
        item: Tuple[str, Type[sob.abc.Model]]
    ) -> Tuple[str, sob.abc.Meta, str, str]:
        line: str
        return (
            item[0],
            sob.meta.read(item[1]),
            "\n".join(
                map(
                    lambda line: line[4:] if line.startswith("    ") else line,
                    (item[1].__doc__ or "").strip().split("\n"),
                )
            ),
            sob.utilities.inspect.get_source(item[1])
            .partition("super().__init__(_data)")[2]
            .strip(),
        )

    return map(get_name_metadata, iter_source_names_models())


def iter_models_metadata_suffixes() -> Iterable[
    Tuple[Type[sob.abc.Model], sob.abc.Meta, str]
]:
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
            yield sob.model.from_meta(
                name,
                metadata,
                module="oapi.oas.model",
                docstring=docstring.strip(),
            ), metadata, suffix


def main() -> None:
    suffix: str
    cls: Type[sob.abc.Model]
    metadata: sob.abc.Meta
    imports: Set[str] = set()
    classes: List[str] = []
    metadatas: List[str] = []
    for cls, metadata, suffix in iter_models_metadata_suffixes():
        import_source: str
        class_source: str
        import_source, _, class_source = (
            sob.utilities.inspect.get_source(cls)
            .replace("oapi.oas.model.", "")
            .rpartition("\n\n\n")
        )
        class_source = re.sub(
            r"\bsob\.model\.Object\b",
            "ExtensibleObject",
            class_source,
        )
        if suffix:
            class_source = f"{class_source.rstrip()}\n        {suffix}"
        if import_source:
            imports |= set(import_source.strip().split("\n"))
        classes.append(class_source.strip())
        assert isinstance(
            metadata,
            (sob.abc.ObjectMeta, sob.abc.ArrayMeta, sob.abc.DictionaryMeta),
        )
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
    model_source: str = "\n\n".join(
        chain(
            (
                "\n".join(
                    chain(
                        (f'"""{model.__doc__.rstrip()}\n"""',),
                        sorted(imports),
                    )
                ),
            ),
            (get_region_source("Base Classes"),),
            ("\n{}\n".format("\n\n\n".join(classes)),),
            ("\n".join(metadatas),),
            (get_region_source("Hooks"),),
        )
    )
    model_source = f"{model_source}\n"
    with open(MODEL_PATH, "w") as model_io:
        model_io.write(model_source)


if __name__ == "__main__":
    main()
