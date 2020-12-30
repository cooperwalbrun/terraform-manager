# Contributing to terraform-manager

1. [Development Workspace Setup](#development-workspace-setup)
2. [Dependency Management](#dependency-management)
    1. [Adding New Dependencies](#adding-new-dependencies)
    2. [Updating Dependencies](#updating-dependencies)
4. [Unit Testing](#unit-testing)
5. [Running terraform-manager Locally](#running-terraform-manager-locally)
6. [Formatting Code](#formatting-code)
    1. [YAPF](#yapf)
    2. [Type Annotations](#type-annotations)
    3. [Imports](#imports)
7. [Changelog](#changelog)

## Development Workspace Setup

To start development and testing, ensure you have Python >=3.6 and <4.0 installed,
[activate the virtual environment](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments)
with something like

```bash
$ python -m venv venv
$ source venv/Scripts/activate
```

Then, run one of the following commands in this project's root directory:

```bash
pip install -e .[development] # Development and unit testing purposes
pip install -e .[testing]     # Unit testing purposes only
```

In order to use the `update-requirements.sh` script mentioned elsewhere in this document, you need
to be able to run Bash scripts (and Linux commands such as `sed`). On Windows machines, this can
easily be achieved using the Git Bash command line, which can be installed as part of
[Git for Windows](https://gitforwindows.org/).

## Dependency Management
 
You may need to occasionally update your environment's `pip-tools` in order for the `pip-compile`
command in `update-requirements.sh` to run smoothly. In general, try to stay on the latest version
of `pip-tools` unless this file documents otherwise. Updating `pip-tools` is as simple as running
the following:

```bash
pip install --upgrade pip-tools
```

### Adding New Dependencies

Before issuing these commands, **ensure that you are in the virtual environment** and that you
executed the `pip install` command intended for development purposes (see
[Development Workspace Setup](#development-workspace-setup)).

1. Add the package to your environment.
    ```properties
    pip install <package> # Adds the package to your virtual environment
    ```

2. Test the dependency out (i.e. write your code) to ensure it satisfies your needs and that it
   works well with existing dependencies.

3. Add a reference to the package in the appropriate place(s). You must do only **one** of the tasks
   below.
    * If it is a **unit testing-only** dependency, add it under `testing =` in `setup.cfg` and
      `deps =` in `tox.ini`.
    * If it is a **testing and development** dependency, add it under `development =` in
      `setup.cfg`.
    * If it is specific to a **GitHub Actions** workflow, add it under `github_actions =` in
      `setup.cfg`.
    * If it is a **production/runtime** dependency, add it under `install_requires =` in
      `setup.cfg`. Unless you know lower versions will work too, specify the version you installed
      as a lower bound (e.g. `somemodule>=X.Y.Z`). Either way, be sure to specify a lower bound (and
      an upper bound, if applicable).
    
4. Update the `requirements/*.txt` files accordingly. All you need to do for this is run the
   `update-requirements.sh` Bash script.

### Updating Dependencies

>Before issuing a `putup --update` command to update PyScaffold, be sure to review the comments in
>setup.py. After issuing `putup --update`, ensure that the `setuptools` version restrictions in
>`setup.py` and `pyproject.toml` are identical.

**Ensure that you are in the virtual environment before issuing these commands.** Also, note that
the `update-requirements.sh` script will only update the `requirements/*.txt` files. You will still
have to execute a `pip install` command (also shown below) to update what is actually installed in
your virtual environment.

```bash
bash update-requirements.sh             # Updates the requirements TXT files using pip-compile
pip install -r requirements/linux.txt   # If your operating system is Linux-based
pip install -r requirements/windows.txt # If your operating system is Windows-based
```

If the new version of the dependency is needed in order for the program to function, be sure to
update the `install_requires` segment of `setup.cfg`.

>You should avoid using the `pip-sync` command to update your dependencies, as this will destroy
>your workspace's development-friendly install of `terraform-manager`, making you unable to use the
>program locally. Use only the `pip install` command as shown above when installing/updating
>dependencies.

## Unit Testing

To run the unit tests, **ensure you are in the virtual environment** with development or testing
dependencies installed (see above) if running tests via `setup.py`, otherwise ensure you are **not**
in a virtual environment if running tests via `tox`. Then, run the corresponding command in this
project's root directory:

```properties
python setup.py test # Run unit tests using your current virtual environment's Python interpreter
tox                  # Run unit tests using tox (requires that you have the necessary Python interpreters on your machine)
```

## Running terraform-manager Locally

To run the program as a CLI tool in your local development environment, you can use a command such
as the following (`--summary` operation for demonstrative purposes):

```bash
python -m terraform_manager -o example123 --summary
```

Beware attempting to run the "watcher" functionality of `terraform-manager` (e.g. `--watch-runs`)
using IDE tooling. You may experience the TUI not appearing at all; if this happens, you should
instead run the command for the watcher directly in a terminal. This is a known limitation when
using IntelliJ IDEA's built-in "Run/Debug Configurations" mechanism, but may apply to other IDEs as
well.

## Formatting Code

### YAPF

This project uses [yapf](https://github.com/google/yapf) to handle formatting, and contributions to
its code are expected to be formatted with YAPF (within reason) using the settings in
[.style.yapf](.style.yapf).

If YAPF is mangling your code in an unmaintainable fashion, you can selectively disable it using the
comments `# yapf: disable` and `# yapf: enable`. Whenever the former appears, the latter must appear
afterwards (this project will not tolerate disabling YAPF for large code blocks and/or entire
files). Disabling YAPF should be done sparingly.

### Type Annotations

In addition to YAPF formatting, code should be appropriately accompanied by type annotations. This
includes:
* Variables and constants in global scope (regardless of whether the variable name is prefixed with
  an underscore)
* All method parameters and method return values
* Any declaration that may have a non-obvious, ambiguous, or otherwise complex type signature

### Imports

Imports should be sorted. Most IDEs support this functionality via keybindings or even via on-save
operations.

## Changelog

This project uses a [CHANGELOG.md](CHANGELOG.md) to track changes. Please update this document along
with your changes when you make a pull request (you can place your changes beneath the `Unreleased`
section near the top). Please also tag your line items with a reference to your GitHub profile. You
should use the formatting that is already in place (see the document for more information).
