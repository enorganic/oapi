from collections import deque
import os
from typing import List
from daves_dev_tools.git.download import download

PROJECT_PATH: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT_URL: str = "https://github.com/OAI/OpenAPI-Specification.git"


def main() -> None:
    files: List[str] = download(
        GIT_URL,
        files=("schemas/v2.*/**", "schemas/v3.*/**"),
        directory=PROJECT_PATH,
    )
    assert files, f"Could not download schemas from {GIT_URL}"
    deque(map(print, files), maxlen=0)


if __name__ == "__main__":
    main()
