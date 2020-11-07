# terraform-manager ![master](https://github.com/cooperwalbrun/terraform-manager/workflows/master/badge.svg)

TODO

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
pip install -e .[testing]     # Unit testing-only purposes
```

## Updating Dependencies

>Before issuing a `putup --update` command to update PyScaffold, be sure to review the comments in
>setup.py. After issuing `putup --update`, ensure that the `setuptools` version restrictions in
>`setup.py` and `pyproject.toml` are identical.

Ensure that you are in the virtual environment (see above) before issuing these commands. Also note
that these commands will only update the `requirements.txt`. You will still have to run e.g. `pip`
commands using `requirements.txt` to update what is actually installed.

```bash
pip-compile --upgrade                   # Update all packages
pip-compile --upgrade-package <package> # Update a specific package
```

## Unit Testing

To run the unit tests, ensure you are in the virtual environment (see above) and run one of the
following commands in this project's root directory:

```bash
python setup.py test # Run unit tests using your virtual environment's Python interpreter
tox                  # Run unit tests using tox (one-to-many virtual environments)
```
