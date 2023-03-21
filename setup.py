import json
from pathlib import Path
from setuptools import find_packages, setup


def read(path: Path, encoding: str = None):
    """Read the contents of a text file safely.
    >>> read(Path("project_name") / "VERSION")
    '0.1.0'
    >>> read(Path("README.md"))
    ...
    """

    content = ""
    with path.open(
        mode="r",
        encoding=encoding or "utf8",
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path: Path):
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


def read_package_json() -> dict:
    """Read frontend package.json file, where all the metadata info are stored"""

    package_json = Path(__file__).parent / "frontend" / "package.json"

    with package_json.open("r", encoding="utf-8") as package_file:
        return json.load(package_file)


package_json = read_package_json()


setup(
    name="mario",
    version=package_json["version"],
    description=package_json["description"],
    url=package_json["repository"]["url"],
    long_description=read(Path("README.md")),
    long_description_content_type="text/markdown",
    author=package_json["author"]["name"],
    author_email=package_json["author"]["email"],
    license=package_json["license"],
    packages=find_packages(exclude=["tests", "frontend", ".github"]),
    install_requires=read_requirements(Path("requirements.txt")),
    extras_require={"dev": read_requirements(Path("requirements-dev.txt"))},
    include_package_data=True,
)
