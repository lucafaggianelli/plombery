from pathlib import Path


class InvalidDataPath(Exception):
    path: Path

    def __init__(self, path: Path) -> None:
        message = f"The path {path} is invalid"
        super().__init__(message)
        self.path = path
