# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

Nothing.

## 0.3.1 - 2020-11-26

### Fixed

* The "certain workspaces" message no longer appears inappropriately for the `--version-summary` operation (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.3.0 - 2020-11-26

### Added

* Unit tests (95% code coverage) for `__main__.py` to test CLI interactions (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Changed

* Python interactions with the module are now centered around the new `Terraform` class (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* `README.md` Python usage examples now use the new `Terraform` class (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* CLI functionality now uses the new `Terraform` class under the hood (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* The print width of the version summary's "Workspaces" column was increased from 70 to 80 characters (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.2.0 - 2020-11-22

### Added

* Created workspace `--working-dir` and `--clear-working-dir` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))

### Fixed

* Fixed an issue with the `--patch-versions` operation (by [@cooperwalbrun](https://github.com/cooperwalbrun))

## 0.1.3 - 2020-11-22

### Added

* There are now badges in the `README.md` for PyPI version and code coverage (by [@cooperwalbrun](https://github.com/cooperwalbrun))

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
* Created initial workspace selection functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created initial  workspace `--version-summary` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created initial  workspace `--patch-versions` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created initial  workspace `--lock`/`--unlock` functionality (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created initial  documentation (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`) (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Implemented over 95% code coverage via unit tests (by [@cooperwalbrun](https://github.com/cooperwalbrun))
* Created GitHub Actions workflows for the `master` branch and pull requests respectively (by [@cooperwalbrun](https://github.com/cooperwalbrun))


