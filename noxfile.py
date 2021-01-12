import os
import tempfile

import nox


# Important!
# Install with constraints requires that poetry pyproject.toml file has registered the packages you are going to install
# in the nox sessions. If not, an error would appear that would be similar to:
# ERROR: In --require-hashes mode, all requirements must have their versions pinned with ==. These do not: ...
# Another option is to not use the install_with_constraints function and just do
# session.install("safety"), for example
# or
# session.install(
#         "flake8",
#         "flake8-bandit")
# instead of
# install_with_constraints(session, "safety") and its equivalent with the lint packages


nox.options.sessions = "tests", "lint_CI", "safety"
lint_locations = "tests", "src",

INSTALL_WITH_CONSTRAINTS = False


@nox.session(python="3.7")
def safety(session):
    with tempfile.NamedTemporaryFile(delete=False) as requirements:
        filename = requirements.name
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={filename}",
            external=True,
        )

    if INSTALL_WITH_CONSTRAINTS:
        install_with_constraints(session, "safety")
    else:
        session.install("safety")

    session.run("safety", "check", f"--file={filename}", "--full-report")
    os.remove(filename)


@nox.session(python=["3.7"])
def lint(session):
    args = session.posargs or lint_locations
    if INSTALL_WITH_CONSTRAINTS:
        install_with_constraints(
            session,
            "flake8",
            "flake8-bandit",
            "flake8-black",
            "flake8-bugbear",
            "flake8-import-order",
        )
    else:
        session.install(
            "flake8",
            "flake8-bandit",
            "flake8-black",
            "flake8-bugbear",
            "flake8-import-order",
        )
    session.run("flake8", *args)


@nox.session(python=["3.7"])
def lint_CI(session):
    args = session.posargs or lint_locations
    if INSTALL_WITH_CONSTRAINTS:
        install_with_constraints(
            session,
            "flake8",
            "flake8-bandit",
            "flake8-black",
            "flake8-bugbear",
            "flake8-import-order",
        )
    else:
        session.install(
            "flake8",
            "flake8-bandit",
            "flake8-black",
            "flake8-bugbear",
            "flake8-import-order",
        )
    session.run("flake8", *(args + ("--extend-ignore", "BLK100")))


@nox.session(python="3.7")
def black(session):
    args = session.posargs or lint_locations
    if INSTALL_WITH_CONSTRAINTS:
        install_with_constraints(session, "black")
    else:
        session.install("black")
    session.run("black", *args)


@nox.session(python=["3.7"])
def tests(session):
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.run("pytest", *args)


def install_with_constraints(session, *args, **kwargs):
    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as requirements:
        filename = requirements.name
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={filename}",
            external=True,
        )
        print(filename)
    session.install(f"--constraint={filename}", *args, **kwargs)
    os.remove(filename)
