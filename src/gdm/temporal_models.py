from datetime import date

from gdm import DistributionComponentBase
from pydantic import field_validator
from infrasys import Component
from uuid import UUID


class DeletionModel(Component):
    name: str = ""
    component_uuid: UUID


class AdditionModel(Component):
    name: str = ""
    component: DistributionComponentBase


class EditModel(Component):
    name: str = ""
    component_uuid: UUID
    component_parameters: dict


class TemporalUpdates(Component):
    name: str = ""
    date: date
    deletions: list[DeletionModel] = []
    additions: list[AdditionModel] = []
    edits: list[EditModel] = []


class ModelUpdates(Component):
    updates: list[TemporalUpdates] = []

    @field_validator("updates")
    @classmethod
    def sort_updates_in_chronological_order(cls, v: list[TemporalUpdates]) -> str:
        return sorted(v, key=lambda x: x.date, reverse=False)
