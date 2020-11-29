from typing import Optional, Dict, Union, Any

JSON = Dict[str, Union[str, bool]]

_default_category: str = "terraform"
_default_hcl: bool = False
_default_sensitive: bool = False


# In this class, we intentionally do not store the variable ID in order to simplify the code
# facilitating the idempotent operations found elsewhere (specifically related to JSON serialization
# and deserialization)
class Variable:
    def __init__(
        self,
        *,
        key: str,
        value: str,
        description: str = "",
        category: str = _default_category,
        hcl: bool = _default_hcl,
        sensitive: bool = _default_sensitive
    ):
        self.key = key
        self.value = value
        self.description = description

        if category in ["terraform", "env"]:
            self.category = category
        else:
            self.category = _default_category

        # The HCL option is only available for "terraform" variables (not environment variables)
        self.hcl = hcl if self.category == "terraform" else False
        self.sensitive = sensitive

    def to_json(self) -> JSON:
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "category": self.category,
            "hcl": self.hcl,
            "sensitive": self.sensitive
        }

    @staticmethod
    def from_json(json: JSON) -> Optional[Any]:  # Returns an Optional[Variable]
        if "key" in json and "value" in json:
            return Variable(
                key=json["key"],
                value=json["value"],
                description=json.get("description", ""),
                category=json.get("category", _default_category),
                hcl=json.get("hcl", _default_hcl),
                sensitive=json.get("sensitive", _default_sensitive)
            )
        else:
            return None

    def __repr__(self) -> str:
        return ("Variable(key={}, value={}, description={}, category={}, hcl={}, sensitive={})"
                ).format(
                    self.key,
                    "<REDACTED>" if self.sensitive else self.value,
                    self.description,
                    self.category,
                    self.hcl,
                    self.sensitive
                )

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, other) -> bool:
        if isinstance(other, Variable):
            return self.key == other.key
        else:
            return False
