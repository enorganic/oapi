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
            value.__module__ = "__main__"
            yield name, value


def iter_names_metadata_docstrings() -> Iterable[
    Tuple[str, sob.abc.Meta, str]
]:
    def get_name_metadata(
        item: Tuple[str, Type[sob.abc.Model]]
    ) -> Tuple[str, sob.abc.Meta, str]:
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
        )

    return map(get_name_metadata, iter_source_names_models())


def iter_models_metadata() -> Iterable[
    Tuple[Type[sob.abc.Model], sob.abc.Meta]
]:
    name: str
    metadata: sob.abc.Meta
    for name, metadata, docstring in iter_names_metadata_docstrings():
        if metadata:
            yield sob.model.from_meta(
                name,
                metadata,
                module="oapi.oas.model",
                docstring=docstring.strip(),
            ), metadata


def main() -> None:
    cls: Type[sob.abc.Model]
    metadata: sob.abc.Meta
    imports: Set[str] = set()
    classes: List[str] = []
    metadatas: List[str] = []
    for cls, metadata in iter_models_metadata():
        import_source: str
        class_source: str
        import_source, _, class_source = (
            sob.utilities.inspect.get_source(cls)
            .replace("oapi.oas.model.", "")
            .rpartition("\n\n\n")
        )
        if import_source:
            imports |= set(import_source.strip().split("\n"))
        classes.append(class_source.strip())
        assert isinstance(
            metadata,
            (sob.abc.ObjectMeta, sob.abc.ArrayMeta, sob.abc.DictionaryMeta),
        )
        if isinstance(metadata, sob.abc.ObjectMeta):
            metadatas.append(
                sob.thesaurus.get_class_meta_attribute_assignment_source(
                    cls.__name__, "properties", metadata
                )
            )
        elif isinstance(metadata, sob.abc.ArrayMeta):
            metadatas.append(
                sob.thesaurus.get_class_meta_attribute_assignment_source(
                    cls.__name__, "item_types", metadata
                )
            )
        else:
            metadatas.append(
                sob.thesaurus.get_class_meta_attribute_assignment_source(
                    cls.__name__, "value_types", metadata
                )
            )
    print(
        "\n\n".join(
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
    )


if __name__ == "__main__":
    main()
