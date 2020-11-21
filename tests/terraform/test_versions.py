import os
import random
import string
from typing import List
from unittest.mock import MagicMock, call

import responses
from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.versions import group_by_version, write_version_summary, \
    VersionSummary, check_versions, patch_versions


def _workspace(version: str) -> Workspace:
    letters = string.ascii_lowercase
    return Workspace(
        "".join([random.choice(letters) for _ in range(5)]),
        "".join([random.choice(letters) for _ in range(5)]),
        version,
        False,
        False
    )


_test_organization: str = "test"
_test_terraform_domain: str = "app.terraform.io"
_test_api_url: str = f"https://{_test_terraform_domain}/api/v2"

_0_12_28: Workspace = _workspace("0.12.28")
_0_13_1_first: Workspace = _workspace("0.13.1")
_0_13_1_second: Workspace = _workspace("0.13.1")
_0_13_5: Workspace = _workspace("0.13.5")
_workspaces: List[Workspace] = [_0_12_28, _0_13_1_first, _0_13_1_second, _0_13_5]
_groups: VersionSummary = group_by_version(_workspaces)
# yapf: disable
_version_table_data: List[List[str]] = [
    ["0.13.5", _0_13_5.name],
    ["0.13.1", ", ".join(sorted([_0_13_1_first.name, _0_13_1_second.name]))],
    ["0.12.28", _0_12_28.name]
]
# yapf: enable

_version_summary_statement: str = (
    f'Terraform version summary for organization "{_test_organization}" at '
    f'"{_test_terraform_domain}":'
)


def test_group_by_version() -> None:
    assert _groups["0.13.5"] == [_0_13_5]
    assert _groups["0.13.1"] == [_0_13_1_first, _0_13_1_second]
    assert _groups["0.12.28"] == [_0_12_28]


def test_check_versions() -> None:
    assert not check_versions(_workspaces, "0.12.27")
    assert not check_versions(_workspaces, "0.13.0")
    assert check_versions(_workspaces, "0.13.5")
    assert check_versions(_workspaces, "0.13.8")


@responses.activate
def test_patch_versions(mocker: MockerFixture) -> None:
    test_version = "0.13.5"
    error_json = {"data": {"id": _0_13_5.workspace_id}}
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")
    responses.add(
        responses.PATCH,
        f"{_test_api_url}/workspaces/{_0_13_1_first.workspace_id}",
        json={"data": {
            "id": _0_13_1_first.workspace_id
        }},
        status=200
    )
    responses.add(
        responses.PATCH,
        f"{_test_api_url}/workspaces/{_0_13_5.workspace_id}",
        json=error_json,
        status=500
    )
    print_mock: MagicMock = mocker.patch("builtins.print")
    patch_versions(
        _test_terraform_domain, [_0_13_1_first, _0_13_5], test_version, write_output=True
    )
    # yapf: disable
    print_mock.assert_has_calls([
        call(
            tabulate(
                [
                    [
                        _0_13_5.name,
                        _0_13_5.terraform_version,
                        test_version,
                        "error",
                        str(error_json)
                    ],
                    [
                        _0_13_1_first.name,
                        _0_13_1_first.terraform_version,
                        test_version,
                        "success",
                        "none"
                    ]
                ],
                headers=["Workspace", "Version Before", "Version After", "Status", "Message"],
                colalign=("left", "right", "right"))

        )
    ])
    # yapf: enable


def test_write_version_summary(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    write_version_summary(_test_terraform_domain, _test_organization, False, _groups)
    print_mock.assert_has_calls([
        call(_version_summary_statement),
        call(),
        call(
            tabulate(_version_table_data, headers=["Version", "Workspaces"], colalign=("right", ))
        )
    ])


def test_write_version_summary_filtered(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    write_version_summary(_test_terraform_domain, _test_organization, True, _groups)
    print_mock.assert_has_calls([
        call(_version_summary_statement),
        call(),
        call(
            tabulate(_version_table_data, headers=["Version", "Workspaces"], colalign=("right", ))
        ),
        call(f"{os.linesep}Note: information is only being displayed for certain workspaces.")
    ])


def test_write_version_summary_single_version(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    write_version_summary(_test_terraform_domain, _test_organization, False, {"0.13.5": [_0_13_5]})
    print_mock.assert_has_calls([
        call(_version_summary_statement),
        call(),
        call(
            tabulate([["0.13.5", "All"]], headers=["Version", "Workspaces"], colalign=("right", ))
        )
    ])
