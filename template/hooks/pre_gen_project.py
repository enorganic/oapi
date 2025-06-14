import re
from re import Pattern

PROJECT_NAME_REGEX: str = r"^[a-z][a-z0-9\-]*[a-z0-9]$"
PROJECT_NAME_PATTERN: Pattern = re.compile(PROJECT_NAME_REGEX)
PACKAGE_NAME_REGEX: str = r"^[a-z][._a-z0-9]*[a-z0-9]$"
PACKAGE_NAME_PATTERN: Pattern = re.compile(PACKAGE_NAME_REGEX)
PROJECT_NAME: str = "{{cookiecutter.project_name}}"
PACKAGE_NAME: str = "{{cookiecutter.package}}"
PACKAGE_DIRECTORY: str = "{{cookiecutter.package_directory}}"


def main() -> None:
    message: str
    if not PACKAGE_DIRECTORY.startswith("src/"):
        message = (
            f"{PACKAGE_DIRECTORY!r} is not a valid package directory. "
            "Package directories must start with 'src/'."
        )
        raise ValueError(message)
    if not PROJECT_NAME_PATTERN.match(PROJECT_NAME):
        message = (
            f"{PROJECT_NAME!r} is not a valid project name. "
            "Project names must match the following regular expression: "
            f"{PROJECT_NAME_REGEX!r}"
        )
        raise ValueError(message)
    if not PACKAGE_NAME_PATTERN.match(PACKAGE_NAME):
        message = (
            f"{PACKAGE_NAME!r} is not a valid package name. "
            "Package names must match the following regular expression: "
            f"{PACKAGE_NAME_REGEX!r}"
        )
        raise ValueError(message)


if __name__ == "__main__":
    main()
