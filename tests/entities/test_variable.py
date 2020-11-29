from typing import Dict, Any

from terraform_manager.entities.variable import Variable

_test_json: Dict[str, Any] = {
    "key": "key",
    "value": "value",
    "description": "",
    "sensitive": True,
    "category": "terraform",
    "hcl": False
}
_test_variable: Variable = Variable(
    key="key", value="value", description="", category="terraform", hcl=False, sensitive=True
)


def test_serialization() -> None:
    assert _test_variable.to_json() == _test_json


def test_deserialization() -> None:
    variable = Variable.from_json(_test_json)
    assert variable.key == _test_json["key"]
    assert variable.value == _test_json["value"]
    assert variable.description == _test_json["description"]
    assert variable.sensitive == _test_json["sensitive"]
    assert variable.category == _test_json["category"]
    assert variable.hcl == _test_json["hcl"]


def test_string_representation_redacts_sensitive_data() -> None:
    assert str(_test_variable) == (
        "Variable(key=key, value=<REDACTED>, description=, category=terraform, hcl=False, "
        "sensitive=True)"
    )
    assert repr(_test_variable) == str(_test_variable)
