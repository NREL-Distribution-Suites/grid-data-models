"""Defines models that can be used for testing the package."""

from typing import Any

from infrasys import Component, Location, System


class SimpleBus(Component):
    """Represents a bus."""

    voltage: float
    coordinates: Location | None = None

    @classmethod
    def example(cls) -> "SimpleBus":
        return SimpleBus(
            name="simple-bus",
            voltage=1.1,
            coordinates=Location(x=0.0, y=0.0),
        )


class GeneratorBase(Component):
    """Base class for generators"""

    available: bool
    bus: SimpleBus


class SimpleGenerator(GeneratorBase):
    """Represents a generator."""

    active_power: float
    rating: float

    @classmethod
    def example(cls) -> "SimpleGenerator":
        return SimpleGenerator(
            name="simple-gen",
            available=True,
            bus=SimpleBus.example(),
            active_power=1.0,
            rating=0.0,
        )


class RenewableGenerator(GeneratorBase):
    """Represents a generator."""

    active_power: float
    rating: float

    @classmethod
    def example(cls) -> "RenewableGenerator":
        return RenewableGenerator(
            name="renewable-gen",
            available=True,
            bus=SimpleBus.example(),
            active_power=1.0,
            rating=0.0,
        )


class SimpleSubsystem(Component):
    """Represents a subsystem."""

    generators: list[SimpleGenerator]

    @classmethod
    def example(cls) -> "SimpleSubsystem":
        return SimpleSubsystem(
            name="simple-subsystem",
            generators=[SimpleGenerator.example()],
        )


class SimpleSystem(System):
    """System used for testing"""

    def __init__(self, my_attr=5, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data_format_version = "1.0.3"
        self.my_attr = my_attr

    def serialize_system_attributes(self) -> dict[str, Any]:
        return {"my_attr": self.my_attr}

    def deserialize_system_attributes(self, data: dict[str, Any]) -> None:
        self.my_attr = data["my_attr"]


if __name__ == "__main__":
    system = SimpleSystem()
    bus = SimpleBus.example()
    gen = SimpleGenerator.example()
    system.add_components(bus, gen)
    bus2 = system.get_component(SimpleBus, "simple-bus")
    gen2 = SimpleGenerator(name="gen2", active_power=3.0, rating=1.0, bus=bus2, available=True)
