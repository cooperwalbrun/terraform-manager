# Contributing to terraform-manager

## Development Workspace Setup

To start development and testing, ensure you have Python 3.x installed,
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

## Adding New Dependencies

Ensure that you are in the virtual environment (see above) before issuing these commands.

1. Add the package to your environment.
    ```bash
    pip install <package> # Adds the package to your virtual environment
    ```

2. Add a reference to the package in the appropriate place(s). You must do only **one** of the tasks
   below.
    * If it is a **unit testing-only** dependency, add it under `testing =` in `setup.cfg` and
      `deps =` in `tox.ini`.
    * If it is a **testing and development** dependency, add it under `development =` in
      `setup.cfg`.
    * If it is a **production/runtime** dependency, add it under `install_requires =` in
      `setup.cfg`.
    
3. Update `requirements.txt` accordingly. All you need to do for this is execute the `pip-compile`
   command.

## Updating Dependencies

>Before issuing a `putup --update` command to update PyScaffold, be sure to review the comments in
>setup.py. After issuing `putup --update`, ensure that the `setuptools` version restrictions in
>`setup.py` and `pyproject.toml` are identical.

Ensure that you are in the virtual environment (see above) before issuing these commands. Also, note
that these commands will only update the `requirements.txt`. You will still have to execute a
`pip install` command to update what is actually installed in your virtual environment.

```bash
pip-compile --upgrade                   # Update all packages
pip-compile --upgrade-package <package> # Update a specific package
pip install -r requirements.txt         # Run this after running either of the above
```

## Unit Testing

To run the unit tests, ensure you are in the virtual environment with development or testing
dependencies installed (see above) and run one of the following commands in this project's root
directory:

```bash
python setup.py test # Run unit tests using your virtual environment's Python interpreter
tox                  # Run unit tests using tox (multiple virtual environments)
```
