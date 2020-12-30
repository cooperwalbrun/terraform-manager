# terraform-manager ![master](https://github.com/cooperwalbrun/terraform-manager/workflows/master/badge.svg) ![PyPI](https://img.shields.io/pypi/v/terraform-manager) ![Code Coverage](https://img.shields.io/badge/coverage-over%2095%25-blue)

1. [Overview](#overview)
    1. [Feature Summary](#feature-summary)
    2. [Limitations](#limitations)
2. [Installation](#installation)
3. [Configuration](#configuration)
    1. [Terraform CLI Configuration](#terraform-cli-configuration)
    2. [Environment Variable Storing the Credentials File Location](#environment-variable-storing-the-credentials-file-location)
    3. [Environment Variable Storing the Token](#environment-variable-storing-the-token)
4. [Usage (CLI)](#usage-cli)
    1. [Selecting Workspaces (CLI)](#selecting-workspaces-cli)
    2. [Operations (CLI)](#operations-cli)
        1. [Variables](#variables)
        2. [Run Watcher](#run-watcher)
5. [Usage (Python)](#usage-python)
    1. [Selecting Workspaces (Python)](#selecting-workspaces-python)
    2. [Operations (Python)](#operations-python)
6. [Contributing](#contributing)

## Overview

`terraform-manager` is a multipurpose Python module and CLI tool for managing Terraform workspaces
in batch fashion. It is specifically designed to help Terraform administrators manage arbitrarily
many workspaces at once. It is also compatible with both Terraform Cloud and Terraform Enterprise,
so regardless of what you or your company is using, this tool can provide value.

### Feature Summary

Here is a (non-exhaustive) outline of `terraform-manager`'s features:

* Use of Terraform API v2
* Adherence to Terraform's API rate limits
* Automatic pagination for applicable Terraform API endpoints (when your organization has enough
  workspaces to mandate pagination)
* Designed to either be usable as a CLI tool or called directly from Python code:
    * System exits are centralized at the CLI entrypoint
    * All console output is suppressed by default (opt-in)
    * All documented Python operations are also available via the CLI
* Flexible credential configuration (multiple ways to specify your Terraform token)
* Powerful functionality for selecting an organization's workspaces to target with operations:
    * Select workspaces in either whitelist or blacklist style
    * Select workspaces using [Unix-like name pattern matching](https://docs.python.org/3/library/fnmatch.html)
* Numerous operations available:
    * View a high-level summary of selected workspaces
    * Watch all workspace run activity in near-real-time
    * Bulk update/create/delete variables of selected workspaces (with idempotency)
    * Bulk update settings of selected workspaces:
        * Terraform version
        * Lock state
        * Working directory
        * Execution mode
        * Auto-apply
        * Speculative runs
* Designed with safety in mind:
    * The Python API of this module has built-in validation to prevent unsafe/invalid HTTP requests to the Terraform API
    * `terraform-manager` will never leak your Terraform token to the console, even if an error occurs

### Limitations

* Due to the rate-limiting restrictions imposed by the Terraform API, this module does not
  officially support execution in a multi-threaded fashion (the rate limit is enforced by blocking
  on the current thread until requests can be sent safely)
* `terraform-helper` is only tested against Python 3.6, 3.7, 3.8, and 3.9, so these are the only
  supported Python distributions

## Installation

If you have Python >=3.6 and <4.0 installed, `terraform-manager` can be installed from PyPI using
something like

```bash
pip install terraform-manager
```

>Note: if you are planning to target a Terraform Enterprise installation that uses a private CA for
>SSL/TLS, you may have to import your custom client certificate(s) into `certifi`'s `cacert.pem`
>before `terraform-manager` operations will function properly. Make sure you modify the version of
>`certifi` that `terraform-manager` uses.

An example of including a custom certificate in `certifi` may look something like this (beware
virtual environments):

```bash
cat your-certificate.crt >> $(python -m certifi)
```

This command would need to be re-run every time you update `terraform-manager` *and* it includes an
underlying `certifi` version change.

## Configuration

All that needs to be configured in order to use this module is a token or credentials file for
interacting with the Terraform API. There are several ways to do this described below.

The order of precedence for these approaches is as follows:

1. (Python only) Pass a token to the constructor of the `Terraform` class (see
   [Usage (Python)](#usage-python) below)
2. Environment Variable Storing the Token
3. Terraform CLI Configuration
4. Environment Variable Storing the Credentials File Location

For options 3 and 4, there is corresponding
[documentation from HashiCorp](https://www.terraform.io/docs/commands/cli-config.html).

### Terraform CLI Configuration

If you have previously configured the Terraform CLI on your machine and subsequently logged into the
target Terraform domain (cloud or enterprise), `terraform-manager` will automatically use your
pre-existing token (stored on your machine by Terraform itself) to make API calls.

### Environment Variable Storing the Credentials File Location

The `TF_CLI_CONFIG_FILE` environment variable may be used to explicitly specify the path to a
file containing your Terraform token. Note that the file must be in HashiCorp's JSON credentials
file format.

### Environment Variable Storing the Token

You can optionally specify the `TERRAFORM_TOKEN` environment variable with the actual value of your
token. This environment variable is specific to `terraform-manager`.

## Usage (CLI)

You can issue the `terraform-manager -h` command to view a manual of available arguments and how
they work together.

All ensuing examples use a Terraform organization name of `example123`.

### Selecting Workspaces (CLI)

```properties
# Select all workspaces in example123
terraform-manager -o example123 <operation>

# Select all workspaces in example123 (all API interactions will use HTTP instead of HTTPS)
terraform-manager -o example123 --no-tls <operation>

# Select all workspaces in example123 at a custom domain
terraform-manager -o example123 --domain something.mycompany.com <operation>

# Select only workspaces with names "workspace1" or "workspace2" (case-insensitive)
terraform-manager -o example123 -w workspace1 workspace3 <operation>

# Select workspaces that begin with "aws" (case-insensitive)
terraform-manager -o example123 -w aws* <operation>

# Select workspaces that do NOT begin with "aws" (case-insensitive)
terraform-manager -o example123 -w aws* -b <operation>
```

### Operations (CLI)

>Note: the operations shown below can be combined with the selection arguments shown above.

```properties
# Print a workspace summary to STDOUT
terraform-manager -o example123 --summary

# Upgrade workspace versions to 0.13.5 and write a report to STDOUT
terraform-manager -o example123 --terraform-version 0.13.5

# Upgrade workspace versions to 0.13.5 and suppress all output (the -s flag works with all operations)
terraform-manager -o example123 --terraform-version 0.13.5 -s

# Lock workspaces and write a report to STDOUT
terraform-manager -o example123 --lock

# Unlock workspaces and write a report to STDOUT
terraform-manager -o example123 --unlock

# Set working directories to "dev" and write a report to STDOUT
terraform-manager -o example123 --working-dir dev

# Set working directories to empty and write a report to STDOUT
terraform-manager -o example123 --clear-working-dir

# Set the execution mode to "local" and write a report to STDOUT
terraform-manager -o example123 --execution-mode local

# Set the execution mode to "agent" with an agent pool ID (required) and write a report to STDOUT
terraform-manager -o example123 --execution-mode agent,apool-ZjT6A7mVFm5WHT5a

# Enable auto-apply and write a report to STDOUT
terraform-manager -o example123 --enable-auto-apply

# Disable auto-apply and write a report to STDOUT
terraform-manager -o example123 --disable-auto-apply

# Enable speculative runs and write a report to STDOUT
terraform-manager -o example123 --enable-speculative

# Disable speculative runs and write a report to STDOUT
terraform-manager -o example123 --disable-speculative

# Delete variables with keys "some-key" and "other-key"
terraform-manager -o example123 --delete-vars some-key other-key
```

#### Variables

The variable configuration operation is a bit different from the ones above; the input to it is a
JSON file containing the variables you wish to define. The contents of this file should consist only
of a JSON array containing one or more JSON objects. To generate an example `template.json` file,
you may issue the following:

```bash
terraform-manager --create-vars-template
```

Note the absence of workspace selection arguments, such as organization. This is a special operation
that takes no other arguments, and it does not interact with the Terraform API at all. After you
configure a JSON file (with a location and name of your choosing), you may pass it to the
`--configure-vars` argument like so:

```bash
terraform-manager -o example123 --configure-vars /some/path/my-vars-file.json
```

This will create all the variables defined in `my-vars-file.json` in every selected workspace, and
if any given variable already exists in a workspace (comparison is done by variable key only), it
will be updated in-place to align with your specified configuration.

#### Run Watcher

There is another special operation in the CLI: `--watch-runs`. It may be used as such:

```bash
terraform-manager -o example123 --watch-runs
```

This operation is unique because it launches a TUI (text user interface) that runs directly in your
command prompt, and the TUI will not exit until the process is terminated, e.g. with `Ctrl+C`. The
TUI will repeatedly fetch active run data from the Terraform API on a set interval, so the data will
be near-real-time (i.e. delayed by a few seconds).

The interface is supported on both Windows and Linux operating systems, but there is a caveat to its
usage: if you are using a nonstandard command prompt for your operating system (e.g. Git Bash on
Windows), the TUI may not function properly.

## Usage (Python)

All ensuing examples use a Terraform organization name of `example123`.

### Selecting Workspaces (Python)

```python
from terraform_manager.entities.terraform import Terraform

# Select all workspaces in example123
terraform = Terraform("app.terraform.io", "example123")

# Select all workspaces in example123 (all API interactions will use HTTP instead of HTTPS)
terraform = Terraform("app.terraform.io", "example123", no_tls=True)

# Select all workspaces in example123 using a token (instead of terraform-manager finding a token on its own)
terraform = Terraform("app.terraform.io", "example123", token="YOUR TOKEN")

# Select all workspaces in example123 at a custom domain
terraform = Terraform("something.mycompany.com", "example123")

# Select only workspaces with names "workspace1" or "workspace2" (case-insensitive)
terraform = Terraform("app.terraform.io", "example123", workspace_names=["workspace1", "workspace2"])

# Select workspaces that begin with "aws" (case-insensitive)
terraform = Terraform("app.terraform.io", "example123", workspace_names=["aws*"])

# Select workspaces that do NOT begin with "aws" (case-insensitive)
terraform = Terraform("app.terraform.io", "example123", workspace_names=["aws*"], blacklist=True)
```

After constructing an instance of `Terraform`, you can optionally validate the arguments that you
passed to its constructor. This validation is intended to help you avoid security vulnerabilities
and/or unexpected behavior. Then, you can finally access the selected workspaces as shown below.

```python
terraform = Terraform(...)
if terraform.configuration_is_valid():
    # Do stuff with terraform.workspaces
```

Be aware that `terraform.workspaces` implicitly calls `configuration_is_valid()`, and if the
configuration is not valid, `terraform.workspaces` will always return an empty list without
attempting to query the Terraform API.

### Operations (Python)

>Note: these operations are safe and do not need to be wrapped in a `try`-`except`. They will return
>a boolean value indicating whether all workspace operations succeeded.

```python
from terraform_manager.entities.terraform import Terraform
from terraform_manager.entities.variable import Variable

# Have a list of workspaces fetched using e.g. one of the methods shown above
terraform = Terraform(...)

# Upgrade workspace versions to 0.13.5
success = terraform.set_versions("0.13.5")

# Lock workspaces
success = terraform.lock_workspaces()

# Unlock workspaces
success = terraform.unlock_workspaces()

# Set working directories to "dev"
success = terraform.set_working_directories("dev")

# Set working directories to empty
success = terraform.set_working_directories(None)

# Set the execution mode to "local"
success = terraform.set_execution_modes("local")

# Set the execution mode to "agent" with an agent pool ID (required)
success = terraform.set_execution_modes("agent", agent_pool_id="apool-ZjT6A7mVFm5WHT5a")

# Enable auto-apply
success = terraform.set_auto_apply(True)

# Disable auto-apply
success = terraform.set_auto_apply(False)

# Enable speculative runs
success = terraform.set_speculative(True)

# Disable speculative runs
success = terraform.set_speculative(False)

# Delete variables with keys "some-key" and "other-key"
success = terraform.delete_variables(["some-key", "other-key"])

# Configure variables (first create a list of one or more variable objects, then configure them)
variables = [
    Variable(key="some-key", value="not-secret"),
    Variable(key="other-key", value="secret", sensitive=True),
    Variable(key="yet-another-key", value="example", category="env")
]
success = terraform.configure_variables(variables) # See below for more information on this method
```

The `Variable` class is similar to the `Terraform` class in that it has built-in validation
functionality. It is recommended to check whether your variables are valid before attempting to
configure them:

```python
variables = [Variable(key="some-key", value="not-secret")]
if all([var.is_valid for var in variables]):
    terraform.configure_variables(variables)
```

Similar to the `Terraform` class's `workspaces` property (which performs automatic validation on the
`Terraform` class), `configure_variables` will internally access the `is_valid` property of each
variable. If any variable is invalid, no variables will be configured and the method will return
`False`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for developer-oriented information.
