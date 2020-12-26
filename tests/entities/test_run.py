from terraform_manager.entities.run import Run

from tests.utilities.tooling import test_run, test_workspace


def test_created_at_unix_time() -> None:
    # yapf: disable
    tests = [
        ("2017-11-28T22:52:46.682Z", 1511909566),
        ("2017-11-28T22:52:46Z", 0)
    ]
    # yapf: enable
    for test, expected_unix_time in tests:
        run = test_run(created_at=test)
        assert run.created_at_unix_time == expected_unix_time


def test_status_unix_time() -> None:
    # yapf: disable
    tests = [
        ({"planned-at": "2020-11-05T04:31:25+00:00"}, 1604550685),
        ({}, 0)
    ]
    # yapf: enable
    for test, expected_unix_time in tests:
        run = test_run(status="planned", all_status_timestamps=test)
        assert run.status_unix_time == expected_unix_time


def test_run_is_active() -> None:
    # yapf: disable
    tests = [
        ("pending", True),
        ("plan_queued", True),
        ("planning", True),
        ("planned", True),
        ("cost_estimating", True),
        ("cost_estimated", True),
        ("policy_checking", True),
        ("policy_override", True),
        ("policy_soft_failed", True),
        ("policy_checked", True),
        ("confirmed", True),
        ("planned_and_finished", False),
        ("apply_queued", True),
        ("applying", True),
        ("applied", False),
        ("discarded", False),
        ("errored", False),
        ("canceled", False),
        ("force_canceled", False)
    ]
    # yapf: enable
    for test, expected_active_status in tests:
        run = test_run(status=test)
        assert run.is_active == expected_active_status


def test_run_equality() -> None:
    (run_id, created_at, status, timestamps) = ("", "", "", {})
    workspace = test_workspace()
    run1 = Run(
        run_id=run_id,
        workspace=workspace,
        created_at=created_at,
        status=status,
        all_status_timestamps=timestamps,
        has_changes=True
    )
    run2 = Run(
        run_id=run_id,
        workspace=workspace,
        created_at=created_at,
        status=status,
        all_status_timestamps=timestamps,
        has_changes=True
    )
    run3 = Run(
        run_id=run_id + "test",
        workspace=workspace,
        created_at=created_at,
        status=status,
        all_status_timestamps=timestamps,
        has_changes=True
    )

    assert run1 == run2
    assert run1 != run3
    assert run1 != "not a run object"
