"""How a pipeline's version is resolved.

The version is recorded on every run, so that a run made before a change can
be told from one made after. It comes from the first source that has an
answer: the pipeline itself, the settings, git. When none of them does, the
version is unknown and nothing is recorded — no substitute identifies the code
a run executed.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from plombery import Pipeline, task
from plombery.config import settings
from plombery.config.model import Settings
from plombery.pipeline.versioning import get_version_from_git

needs_git = pytest.mark.skipif(
    shutil.which("git") is None, reason="git is not installed"
)


@pytest.fixture(autouse=True)
def clean_settings():
    """A version configured for the test run must not leak into the tests."""

    original = settings.pipeline_version
    settings.pipeline_version = None
    yield
    settings.pipeline_version = original


@pytest.fixture
def without_git(monkeypatch: pytest.MonkeyPatch):
    """A pipeline with no repository to be read from — a deployed one."""

    monkeypatch.setattr(
        "plombery.pipeline.pipeline.get_version_from_git",
        lambda directory: None,
    )


def build_pipeline(**kwargs) -> Pipeline:
    pipeline = Pipeline(id="versioned", **kwargs)

    with pipeline:

        @task
        def only_task():
            return 1

    return pipeline


def test_an_explicit_version_wins_over_every_other_source():
    settings.pipeline_version = "from-the-settings"

    assert build_pipeline(version="v2.1.0").get_version() == "v2.1.0"


def test_the_setting_wins_over_git():
    """What a deployment declares is what the deployment is running.

    A checkout mounted into a container still has a repository, but it's the
    build that knows which revision was deployed.
    """

    settings.pipeline_version = "1.4.0"

    assert build_pipeline().get_version() == "1.4.0"


def test_the_setting_is_read_from_the_environment(monkeypatch: pytest.MonkeyPatch):
    """The name a deployment sets, which is the whole point of the setting."""

    monkeypatch.setenv("PIPELINE_VERSION", "3ab1c2d")

    assert Settings().pipeline_version == "3ab1c2d"


@needs_git
def test_git_is_used_when_nothing_else_is_set():
    """Development: the repository defining the pipeline is right there.

    The tasks of `build_pipeline` are defined in this very file, so the
    repository to describe is the one holding the tests.
    """

    version = build_pipeline().get_version()

    assert version == get_version_from_git(str(Path(__file__).parent))


def test_no_source_leaves_the_version_unknown(without_git):
    """Neither the shape of the graph nor anything else stands in.

    A task can be rewritten from top to bottom without an edge moving, so a
    version derived from the graph would claim two different runs executed the
    same code.
    """

    assert build_pipeline().get_version() is None


def test_no_repository_yields_no_git_version(tmp_path):
    """A folder outside any repository — a container's `/app`, typically."""

    get_version_from_git.cache_clear()

    assert get_version_from_git(str(tmp_path)) is None


@needs_git
def test_the_git_version_describes_the_repository(tmp_path):
    _init_repository(tmp_path)
    subprocess.run(
        ["git", "tag", "v3.0.0"], cwd=tmp_path, check=True, capture_output=True
    )

    get_version_from_git.cache_clear()

    assert get_version_from_git(str(tmp_path)) == "v3.0.0"


@needs_git
def test_a_repository_is_found_from_a_subfolder(tmp_path):
    _init_repository(tmp_path)

    pipelines_folder = tmp_path / "src" / "pipelines"
    pipelines_folder.mkdir(parents=True)

    get_version_from_git.cache_clear()

    assert get_version_from_git(str(pipelines_folder)) is not None


def _init_repository(directory) -> None:
    subprocess.run(["git", "init"], cwd=directory, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@test.test",
            "-c",
            "user.name=test",
            "commit",
            "--allow-empty",
            "-m",
            "first",
        ],
        cwd=directory,
        check=True,
        capture_output=True,
    )
