import os
from pathlib import Path
import re
from typing import Optional

from yaml import load


try:
    # if libyaml is installed
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

ENV_VAR_MATCHER = re.compile(r"\$(\w+|\{[^}]*\})")


def _path_constructor(loader, node):
    return os.path.expandvars(node.value)


class EnvVarLoader(SafeLoader):  # type: ignore
    pass


EnvVarLoader.add_implicit_resolver("!env", ENV_VAR_MATCHER, None)
EnvVarLoader.add_constructor("!env", _path_constructor)


def load_config_file(config_file: Path, encoding: Optional[str] = None) -> dict:
    with config_file.open(mode="r", encoding=encoding or "utf-8") as f:
        # `or {}` because the file may be empty
        return load(f, Loader=EnvVarLoader) or {}
