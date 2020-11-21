# terraform-manager ![master](https://github.com/cooperwalbrun/terraform-manager/workflows/master/badge.svg)

TODO - enumerate features & mention that Terraform API v2 is used

-terraform api v2
-adherence to API rate limits
-automatic pagination for applicable API endpoints
-designed to be used as a CLI tool or called from python code (system exits centralized to __main__.py, console output controlled via function parameters, etc)
    -e.g. parameters write_output, write_error_messages (defaults are always false)
-useful workspace querying capabilities against an organization
    -whitelist and blacklist mechanisms
    -filter-by-name with support for Unix-like filename pattern matching (see https://docs.python.org/3/library/fnmatch.html)
-others?

See [CONTRIBUTING.md](CONTRIBUTING.md) for developer-oriented information.

## Installation

TODO

## Configuration

All that needs to be configured in order to use this module is a token or credentials file for
interacting with the Terraform API. There are several ways to do this; the primary ones are
described below. For the first two options, there is corresponding
[documentation from HashiCorp](https://www.terraform.io/docs/commands/cli-config.html).

### Terraform CLI Configuration

If you have previously configured the Terraform CLI on your machine and subsequently logged into the
target Terraform domain (cloud or enterprise), `terraform-manager` will automatically use your
pre-existing token (stored on your machine by Terraform itself) to make API calls.

### Environment Variable Storing the Credentials File Path

The `TF_CLI_CONFIG_FILE` environment variable may be used to explicitly specify the path to a
file containing your Terraform token. Note that the file must be in HashiCorp's JSON credentials
file format.

### Environment Variable Storing the Token

You can optionally specify the `TERRAFORM_TOKEN` environment variable with the actual value of your
token. This environment variable is specific to `terraform-manager`.

## Usage

TODO
