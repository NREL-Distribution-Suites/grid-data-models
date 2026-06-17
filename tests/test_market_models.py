"""Tests for wholesale market tariff and aggregator data models."""


import pytest

from gdm.distribution.enums import (
    AncillaryServiceType,
    CapacityMarketType,
    CustomerClass,
    Month,
    PricingNodeType,
    WholesaleMarketType,
)
from gdm.distribution.market import (
    AncillaryServiceRate,
    CapacityPayment,
    DistributionTariff,
    LMPRate,
    PricingNode,
    WholesaleMarketTariff,
)
from gdm.distribution.market.aggregator import (
    AggregatedDER,
    AggregatedLoad,
    Aggregator,
    DERAggregator,
    LoadAggregator,
)
from gdm.quantities import ActivePower


# ---------------------------------------------------------------------------
# Wholesale tariff model tests
# ---------------------------------------------------------------------------


class TestLMPRate:
    def test_total_lmp_property(self):
        lmp = LMPRate(energy_rate=30.0, congestion_rate=5.0, loss_rate=2.0)
        assert lmp.total_lmp == pytest.approx(37.0)

    def test_defaults_zero_congestion_and_loss(self):
        lmp = LMPRate(energy_rate=40.0)
        assert lmp.congestion_rate == 0.0
        assert lmp.loss_rate == 0.0
        assert lmp.total_lmp == pytest.approx(40.0)


class TestPricingNode:
    def test_optional_zone(self):
        node = PricingNode(name="N1", node_type=PricingNodeType.HUB)
        assert node.zone is None

    def test_with_zone(self):
        node = PricingNode(name="N2", node_type=PricingNodeType.LOAD_ZONE, zone="WEST")
        assert node.zone == "WEST"


class TestCapacityPayment:
    def test_duplicate_months_rejected(self):
        with pytest.raises(ValueError, match="Duplicate months"):
            CapacityPayment(
                capacity_market_type=CapacityMarketType.FORWARD_CAPACITY,
                rate=100.0,
                commitment_months=[Month.JUNE, Month.JUNE],
            )

    def test_valid_commitment(self):
        cp = CapacityPayment(
            capacity_market_type=CapacityMarketType.RESOURCE_ADEQUACY,
            rate=200.0,
            commitment_months=[Month.JANUARY, Month.FEBRUARY, Month.MARCH],
        )
        assert len(cp.commitment_months) == 3


class TestWholesaleMarketTariff:
    def test_duplicate_ancillary_services_rejected(self):
        dup_rate = AncillaryServiceRate(
            service_type=AncillaryServiceType.REGULATION_UP,
            rate=10.0,
            market_type=WholesaleMarketType.DAY_AHEAD,
        )
        with pytest.raises(ValueError, match="Duplicate ancillary service"):
            WholesaleMarketTariff(
                name="Bad Tariff",
                market_operator="TEST_ISO",
                market_type=WholesaleMarketType.DAY_AHEAD,
                pricing_node=PricingNode.example(),
                lmp_rate=LMPRate.example(),
                ancillary_service_rates=[dup_rate, dup_rate],
            )

    def test_same_service_different_markets_allowed(self):
        tariff = WholesaleMarketTariff(
            name="Multi-Market",
            market_operator="PJM",
            market_type=WholesaleMarketType.DAY_AHEAD,
            pricing_node=PricingNode.example(),
            lmp_rate=LMPRate.example(),
            ancillary_service_rates=[
                AncillaryServiceRate(
                    service_type=AncillaryServiceType.REGULATION_UP,
                    rate=10.0,
                    market_type=WholesaleMarketType.DAY_AHEAD,
                ),
                AncillaryServiceRate(
                    service_type=AncillaryServiceType.REGULATION_UP,
                    rate=15.0,
                    market_type=WholesaleMarketType.REAL_TIME,
                ),
            ],
        )
        assert len(tariff.ancillary_service_rates) == 2

    def test_minimal_tariff(self):
        tariff = WholesaleMarketTariff(
            name="Minimal",
            market_operator="ERCOT",
            market_type=WholesaleMarketType.REAL_TIME,
            pricing_node=PricingNode.example(),
            lmp_rate=LMPRate(energy_rate=25.0),
        )
        assert tariff.capacity_payments is None
        assert tariff.transmission_charges is None


# ---------------------------------------------------------------------------
# Aggregator model tests
# ---------------------------------------------------------------------------


class TestDERAggregator:
    def test_dispatch_limits_validated(self):
        with pytest.raises(ValueError, match="max_dispatch must be >= min_dispatch"):
            DERAggregator(
                name="Bad",
                resources=[AggregatedDER.example()],
                min_dispatch=ActivePower(100, "kilowatt"),
                max_dispatch=ActivePower(10, "kilowatt"),
            )

    def test_with_wholesale_tariff(self):
        agg = DERAggregator(
            name="With Tariff",
            resources=[AggregatedDER.example()],
            min_dispatch=ActivePower(10, "kilowatt"),
            max_dispatch=ActivePower(100, "kilowatt"),
            wholesale_tariff=WholesaleMarketTariff.example(),
        )
        assert agg.wholesale_tariff is not None
        assert agg.wholesale_tariff.market_operator == "PJM"

    def test_without_tariff(self):
        agg = DERAggregator.example()
        assert agg.wholesale_tariff is None


class TestLoadAggregator:
    def test_valid_load_aggregator(self):
        agg = LoadAggregator.example()
        assert len(agg.resources) == 1
        assert agg.retail_tariff is None

    def test_with_retail_tariff(self):
        agg = LoadAggregator(
            name="DR with Tariff",
            resources=[AggregatedLoad.example()],
            total_curtailable_capacity=ActivePower(500, "kilowatt"),
            notification_lead_time_minutes=30,
            max_curtailment_duration_hours=4.0,
            retail_tariff=DistributionTariff.example(),
        )
        assert agg.retail_tariff is not None
        assert agg.retail_tariff.customer_class == CustomerClass.RESIDENTIAL


class TestAggregator:
    def test_no_resources_rejected(self):
        with pytest.raises(ValueError, match="at least one DER or load resource"):
            Aggregator(
                name="Empty",
                min_dispatch=ActivePower(0, "kilowatt"),
                max_dispatch=ActivePower(100, "kilowatt"),
            )

    def test_dispatch_limits_validated(self):
        with pytest.raises(ValueError, match="max_dispatch must be >= min_dispatch"):
            Aggregator(
                name="Bad Limits",
                der_resources=[AggregatedDER.example()],
                min_dispatch=ActivePower(200, "kilowatt"),
                max_dispatch=ActivePower(50, "kilowatt"),
            )

    def test_der_only(self):
        agg = Aggregator(
            name="DER Only",
            der_resources=[AggregatedDER.example()],
            min_dispatch=ActivePower(10, "kilowatt"),
            max_dispatch=ActivePower(100, "kilowatt"),
        )
        assert agg.load_resources is None

    def test_load_only(self):
        agg = Aggregator(
            name="Load Only",
            load_resources=[AggregatedLoad.example()],
            min_dispatch=ActivePower(5, "kilowatt"),
            max_dispatch=ActivePower(50, "kilowatt"),
        )
        assert agg.der_resources is None

    def test_with_both_tariffs(self):
        agg = Aggregator(
            name="Full Portfolio",
            der_resources=[AggregatedDER.example()],
            load_resources=[AggregatedLoad.example()],
            min_dispatch=ActivePower(10, "kilowatt"),
            max_dispatch=ActivePower(200, "kilowatt"),
            wholesale_tariff=WholesaleMarketTariff.example(),
            retail_tariff=DistributionTariff.example(),
        )
        assert agg.wholesale_tariff is not None
        assert agg.retail_tariff is not None
