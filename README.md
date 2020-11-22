# terraform-manager ![master](https://github.com/cooperwalbrun/terraform-manager/workflows/master/badge.svg) ![PyPI](https://img.shields.io/pypi/v/terraform-manager) ![Code Coverage](https://img.shields.io/badge/coverage-over%2095%25-blue)

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
    1. [Terraform CLI Configuration](#terraform-cli-configuration)
    2. [Environment Variable Storing the Credentials File Location](#environment-variable-storing-the-credentials-file-location)
    3. [Environment Variable Storing the Token](#environment-variable-storing-the-token)
4. [Usage (CLI)](#usage-cli)
    1. [Selecting Workspaces (CLI)](#selecting-workspaces-cli)
    2. [Operations (CLI)](#operations-cli)
5. [Usage (Python)](#usage-python)
    1. [Selecting Workspaces (Python)](#selecting-workspaces-python)
    2. [Operations (Python)](#operations-python)
6. [Contributing](#contributing)

## Overview

`terraform-manager` is a multipurpose CLI tool for managing Terraform workspaces in batch fashion.
It is specifically designed to help Terraform administrators manage many workspaces at once. It is
also compatible with both Terraform Cloud and Terraform Enterprise, so regardless of what you or
your company is using, this CLI can provide value.

Here is a (non-exhaustive) outline of `terraform-manager`'s features:

* Use of Terraform API v2
* Adherence to Terraform's API rate limits
* Automatic pagination for applicable Terraform API endpoints (when your organization has enough
  workspaces to mandate pagination)
* Designed to be usable as either a CLI tool or called from Python code:
    * System exits are centralized at the CLI entrypoint
    * All console output is suppressed by default (opt-in)
* Powerful functionality for selecting an organization's workspaces to target with operations:
    * Select workspaces in either whitelist or blacklist style
    * Select workspaces using [Unix-like filename pattern matching](https://docs.python.org/3/library/fnmatch.html)
* Numerous operations available:
    * View a high-level Terraform version summary of selected workspaces
    * Bulk lock or unlock selected workspaces
    * Bulk update the Terraform version of selected workspaces

## Installation

If you have Python >=3.6 and <4.0 installed, `terraform-manager` can be installed from PyPI using
something like

```bash
pip install terraform-manager
```

## Configuration

All that needs to be configured in order to use this module is a token or credentials file for
interacting with the Terraform API. There are several ways to do this; the primary methods are
described below. For the first two options, there is corresponding
[documentation from HashiCorp](https://www.terraform.io/docs/commands/cli-config.html).

The order of precedence for these approaches is as follows:
1. Environment Variable Storing the Token
2. Terraform CLI Configuration
3. Environment Variable Storing the Credentials File Location

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

```bash
# Select all workspaces in example123
terraform-manager example123 <operation>

# Select all workspaces in example123 at a custom domain
terraform-manager example123 --domain something.mycompany.com <operation>

# Select only workspaces with names "workspace1" or "workspace2" (case-insensitive)
terraform-manager example123 <operation> -w workspace1 workspace3

# Select workspaces that begin with "aws" (case-insensitive)
terraform-manager example123 <operation> -w aws*

# Select workspaces that do NOT begin with "aws" (case-insensitive)
terraform-manager example123 <operation> -w aws* -b
```

### Operations (CLI)

>Note: the operations shown below can be combined with the selection arguments shown above.

```bash
# Print a version summary to STDOUT
terraform-manager example123 --version-summary

# Upgrade workspace versions to 0.13.5 and write a report to STDOUT
terraform-manager example123 --patch-versions 0.13.5

# Lock workspaces and write a report to STDOUT
terraform-manager example123 --lock

# Unlock workspaces and write a report to STDOUT
terraform-manager example123 --unlock

# Set working directories to "dev" and write a report to STDOUT
terraform-manager example123 --working-dir dev

# Set working directories to empty and write a report to STDOUT
terraform-manager example123 --clear-working-dir
```

## Usage (Python)

All ensuing examples use a Terraform organization name of `example123`.

### Selecting Workspaces (Python)

>Note: all `fetch_all` operations are safe and do not need to be wrapped in a `try`-`except`.

```python
from typing import List
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.workspaces import fetch_all

# Select all workspaces in example123
workspaces: List[Workspace] = fetch_all("app.terraform.io", "example123")

# Select all workspaces in example123 at a custom domain
workspaces: List[Workspace] = fetch_all("something.mycompany.com", "example123")

# Select only workspaces with names "workspace1" or "workspace2" (case-insensitive)
workspaces: List[Workspace] = fetch_all("app.terraform.io", "example123", workspaces=["workspace1", "workspace2"])

# Select workspaces that begin with "aws" (case-insensitive)
workspaces: List[Workspace] = fetch_all("app.terraform.io", "example123", workspaces=["aws*"])

# Select workspaces that do NOT begin with "aws" (case-insensitive)
workspaces: List[Workspace] = fetch_all("app.terraform.io", "example123", workspaces=["aws*"], blacklist=True)
```

### Operations (Python)

>Note: all operations are safe and do not need to be wrapped in a `try`-`except`.

```python
from typing import List
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.locking import lock_or_unlock_workspaces
from terraform_manager.terraform.versions import patch_versions
from terraform_manager.terraform.working_directories import patch_working_directories
from terraform_manager.terraform.workspaces import fetch_all

# Have a list of workspaces fetched using e.g. one of the methods shown above
domain: str = "app.terraform.io"
organization: str = "example123"
workspaces: List[Workspace] = fetch_all(domain, organization)

# Upgrade workspace versions to 0.13.5
success: bool = patch_versions(domain, organization, workspaces, new_version="0.13.5")

# Lock workspaces
success: bool = lock_or_unlock_workspaces(domain, organization, workspaces, set_lock=True)

# Unlock workspaces
success: bool = lock_or_unlock_workspaces(domain, organization, workspaces, set_lock=False)

# Set working directories to "dev"
success: bool = patch_working_directories(domain, organization, workspaces, new_working_directory="dev")

# Set working directories to empty
success: bool = patch_working_directories(domain, organization, workspaces, new_working_directory=None)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for developer-oriented information.
