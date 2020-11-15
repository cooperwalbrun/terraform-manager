import os
import random
import string
from typing import List
from unittest.mock import MagicMock, call

from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.versions import group_by_version, write_version_summary, \
    VersionSummary


def _workspace(version: str) -> Workspace:
    letters = string.ascii_lowercase
    return Workspace(
        "".join([random.choice(letters) for _ in range(5)]),
        "".join([random.choice(letters) for _ in range(5)]),
        version,
        False,
        False
    )


_0_12_28: Workspace = _workspace("0.12.28")
_0_13_1_first: Workspace = _workspace("0.13.1")
_0_13_1_second: Workspace = _workspace("0.13.1")
_0_13_5: Workspace = _workspace("0.13.5")
_workspaces: List[Workspace] = [_0_12_28, _0_13_1_first, _0_13_1_second, _0_13_5]
_groups: VersionSummary = group_by_version(_workspaces)
# yapf: disable
_table_data: List[List[str]] = [
    ["0.13.5", _0_13_5.name],
    ["0.13.1", ", ".join(sorted([_0_13_1_first.name, _0_13_1_second.name]))],
    ["0.12.28", _0_12_28.name]
]
# yapf: enable


def _first_summary_print_statement(organization: str) -> call:
    return call((
        f'Terraform version summary for organization "{organization}" at '
        f'"app.terraform.io":{os.linesep}'
    ))


def test_group_by_version() -> None:
    assert _groups["0.13.5"] == [_0_13_5]
    assert _groups["0.13.1"] == [_0_13_1_first, _0_13_1_second]
    assert _groups["0.12.28"] == [_0_12_28]


def test_write_version_summary(mocker: MockerFixture) -> None:
    organization = "test"
    print_mock: MagicMock = mocker.patch("builtins.print")
    write_version_summary(organization, False, None, _groups)
    print_mock.assert_has_calls([
        _first_summary_print_statement(organization),
        call(tabulate(_table_data, headers=["Version", "Workspaces"], colalign=("right", )))
    ])


def test_write_version_summary_filtered(mocker: MockerFixture) -> None:
    organization = "test"
    print_mock: MagicMock = mocker.patch("builtins.print")
    write_version_summary(organization, True, None, _groups)
    print_mock.assert_has_calls([
        _first_summary_print_statement(organization),
        call(tabulate(_table_data, headers=["Version", "Workspaces"], colalign=("right", ))),
        call(f"{os.linesep}Note: information is only being displayed for certain workspaces.")
    ])


def test_write_version_summary_single_version(mocker: MockerFixture) -> None:
    organization = "test"
    print_mock: MagicMock = mocker.patch("builtins.print")
    write_version_summary(organization, False, None, {"0.13.5": [_0_13_5]})
    print_mock.assert_has_calls([
        _first_summary_print_statement(organization),
        call(
            tabulate([["0.13.5", "All"]], headers=["Version", "Workspaces"], colalign=("right", ))
        )
    ])
