# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

* Implemented the `--watch-runs` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Updated documentation and `requirements.txt` files to address operating system-specific requirements (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* The `Tags` GitHub Actions workflow now only installs `wheel` (instead of a `requirements.txt`) prior to creating distribution artifacts (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* All `install_requires` dependencies in `setup.cfg` now specify a version lower bound based on `terraform-manager`'s inception date (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## v0.5.2 - 2020-12-13

### Added

* Added a new `is_terraform_cloud` property to the `Terraform` class (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Fixed

* Fixed the implementation of `--execution-mode` to properly handle the `agent` mode via inclusion of an optional `agent-pool-id` (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## v0.5.1 - 2020-12-13

### Added

* The `Variable` class now has an `is_valid` property for ascertaining that the variable could be configured via the Terraform API (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Implemented a generalized `--summary` operation for showing all `terraform-manager`-managed fields for workspaces (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Updated the `Tags` GitHub Actions workflow to use `pip install -r requirements.txt` (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* The reports printed during CLI operations will now wrap the `Message` column at 70 characters (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Removed

* Removed the `--version-summary` operation in favor of the more-general `--summary` operation (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## v0.5.0 - 2020-12-12

### Added

* Added functionality for the `--enable-auto-apply`/`--disable-auto-apply` operations (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Added functionality for the `--enable-speculative`/`--disable-speculative` operations (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Renovated the internal design of batch `PATCH` operations to optimize code reuse; removed no-longer-needed unit tests (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Changed the method name `patch_versions` to `set_versions` in the `Terraform` class (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Renamed the CLI flag `--patch-versions` to `--terraform-version` (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Fixed

* Parser-oriented errors will now respect the presence of the `-s` flag on the CLI (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.4.3 - 2020-12-06

### Added

* Added an optional `-s` CLI flag to tell `terraform-manager` to suppress all output (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Added functionality for the `--execution-mode` operation (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* All operations' reports will now write messages indicating that nothing changed when applicable (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.4.2 - 2020-12-05

### Added

* Added a `configuration_is_valid()` method to the `Terraform` class (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Reorganized CLI operations and started using the new `configuration_is_valid()` method to check CLI parameters (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Updated the argument parser for the CLI to function in a way more consistent with the documentation (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.4.1 - 2020-12-05

### Added

* Implemented the `--delete-vars` operation (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* The `--lock` and `--unlock` operations will now write descriptive messages about prior lock states in the report (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Fixed

* Removed unexpected console output during the `--configure-vars` operation and added unit test assertions to prevent this in the future (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.4.0 - 2020-11-29

### Added

* Implemented the `--create-vars-template` and `--configure-vars` operations (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* The Terraform organization must now be specified via the `-o` argument on the CLI (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Fixed

* Tokens specified inline via the `Terraform` class's constructor are now used for the working directory operations (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.3.2 - 2020-11-27

### Added

* Added an optional `--no-tls` flag to enable Terraform API interactions via HTTP instead of HTTPS (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Added an optional `token` keyword argument to the `Terraform` class's constructor (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Moved the fetch of workspaces out of the constructor of the `Terraform` class; it will now only occur when needed (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.3.1 - 2020-11-26

### Fixed

* The "certain workspaces" message no longer appears inappropriately for the `--version-summary` operation (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.3.0 - 2020-11-26

### Added

* Added unit tests (95% code coverage) for `__main__.py` to test CLI interactions (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Python interactions with the module are now centered around the new `Terraform` class (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* CLI functionality now uses the new `Terraform` class under the hood (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* The print width of the version summary's "Workspaces" column was increased from 70 to 80 characters (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.2.0 - 2020-11-22

### Added

* Created workspace `--working-dir` and `--clear-working-dir` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Fixed

* Resolved the "required positional argument" error in the `--patch-versions` operation (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.1.3 - 2020-11-22

### Added

* Added two badges in the `README.md` for PyPI version and code coverage (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Improved console output formatting for the CLI `--patch-versions` and `--lock`/`--unlock` operations (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.1.2 - 2020-11-22

### Added

* Created a GitHub Actions workflow for automatically publishing tags to PyPI (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.1.1 - 2020-11-22

### Added

* Created the command line entrypoint for the module (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.1.0 - 2020-11-22

### Added

* Created the project using PyScaffold (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created the initial workspace selection functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created the initial workspace `--version-summary` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created the initial workspace `--patch-versions` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created the initial workspace `--lock`/`--unlock` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created the initial documentation (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`) (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Implemented over 95% code coverage via unit tests (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created GitHub Actions workflows for the `master` branch and pull requests respectively (by [@cooperwalbrun](https://github.com/cooperwalbrun))


