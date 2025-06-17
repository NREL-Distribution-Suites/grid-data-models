from collections import Counter

from pydantic import BaseModel, model_validator
from semver import Version

from gdm.distribution.upgrade_handler.from__2_0_1__to__2_1_0 import from__2_0_1__to__2_1_0


class SemanticVersion(Version):
    @classmethod
    def __get_validators__(cls):
        yield cls.parse

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class UpgradeSchema(BaseModel):
    method: callable
    from_version: SemanticVersion
    to_version: SemanticVersion

    class Config:
        arbitrary_types_allowed = True

    @model_validator(mode="after")
    def validate_version(self):
        if self.from_version > self.to_version:
            raise ValueError(
                f"from_version {str(self.from_version)} should be lower than the to_version {str(self.to_version)}"
            )
        return self


class UpgradeHandler(BaseModel):
    upgrade_schemas: list[UpgradeSchema] = [
        UpgradeSchema(
            method=from__2_0_1__to__2_1_0,
            from_version="2.0.1",
            to_version="2.1.0",
        ),
    ]

    @model_validator(mode="after")
    def validate_version(self):
        for attr in ["from_version", "to_version"]:
            versions = [getattr(x, attr) for x in self.upgrade_schemas]
            counts = Counter(versions)
            non_unique_values = [str(item) for item, count in counts.items() if count > 1]
            if len(non_unique_values) != 0:
                raise ValueError(
                    f"All {attr} in 'upgrade_schemas' should be unique. Repeated {attr} values are {non_unique_values}"
                )

        return self

    def _get_upgrade_handlers(self, from_version: str, to_version: str):
        upgrade_handlers = sorted(self.upgrade_schemas, key=lambda x: x.from_version)
        filtered_upgrade_handlers = list(
            filter(lambda x: x.from_version >= from_version, upgrade_handlers)
        )
        final_upgrade_handlers = list(
            filter(lambda x: x.to_version <= to_version, filtered_upgrade_handlers)
        )

        old_handler = None
        for i, handler in enumerate(final_upgrade_handlers):
            if i != 0:
                if handler.from_version != old_handler.to_version:
                    raise ValueError(
                        f"Upgrade chain is broken. Unable to find handler to upgarde from version {str(old_handler.to_version)} to {handler.from_version}"
                    )
            old_handler = handler

        if final_upgrade_handlers[0].from_version != from_version:
            raise ValueError(
                f"Upgrade chain is broken. from_version for upgrade handler should start from version {from_version}"
            )

        if final_upgrade_handlers[-1].to_version != to_version:
            raise ValueError(
                f"Upgrade chain is broken. to_version for upgrade handler should end with version {to_version}"
            )

        return final_upgrade_handlers

    def upgrade(self, data, from_version, to_version):
        handlers = self._get_upgrade_handlers(from_version, to_version)
        for handler in handlers:
            data = handler.method(data, handler.from_version, handler.to_version)
