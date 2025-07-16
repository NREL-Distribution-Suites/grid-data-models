from datetime import time

from pydantic import Field, model_validator
from typing import List, Optional
from infrasys import Component

from gdm.distribution.enums import BillingDemandBasis, CustomerClass, TOUPeriodType, Season


class TOURatePeriod(Component):
    name: str = ""
    start_time: time = Field(..., description="Start time of the rate period")
    end_time: time = Field(..., description="End time of the rate period")
    rate: float = Field(..., gt=0, description="Rate for the period in $/kWh")
    period_type: TOUPeriodType = Field(
        ..., description="Type of the TOU period (peak, off-peak, mid-peak)"
    )

    @model_validator(mode="after")
    def check_time_order(self) -> "TOURatePeriod":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

    @classmethod
    def example(cls) -> "TOURatePeriod":
        return TOURatePeriod(
            start_time=time(14, 0), end_time=time(20, 0), rate=0.25, period_type=TOUPeriodType.PEAK
        )


class DemandCharge(Component):
    name: str = ""
    rate: float = Field(..., gt=0, description="Rate for demand charge in $/kW")
    billing_demand_basis: BillingDemandBasis = Field(
        ..., description="Basis for billing demand calculation"
    )
    time_applicability: Optional[List[TOURatePeriod]] = Field(
        ..., description="Time periods when the demand charge applies"
    )

    @classmethod
    def example(cls) -> "DemandCharge":
        return DemandCharge(
            rate=12.50,
            billing_demand_basis=BillingDemandBasis.PEAK_15MIN,
            time_applicability=[TOURatePeriod.example()],
        )


class SeasonalTOURates(Component):
    name: str = ""
    season: Season = Field(..., description="Season for the TOU rates")
    tou_periods: List[TOURatePeriod] = Field(..., description="List of TOU periods for the season")

    @classmethod
    def example(cls) -> "SeasonalTOURates":
        return SeasonalTOURates(
            season=Season.SUMMER,
            tou_periods=[
                TOURatePeriod.example(),
                TOURatePeriod(
                    start_time=time(20, 0),
                    end_time=time(23, 59),
                    rate=0.15,
                    period_type=TOUPeriodType.OFF_PEAK,
                ),
            ],
        )


class TieredRate(Component):
    name: str = ""
    upper_limit_kwh: float = Field(..., gt=0, description="Upper limit of the tier in kWh")
    rate: float = Field(..., gt=0, description="Rate for the tier in $/kWh")

    @classmethod
    def example(cls) -> "TieredRate":
        return TieredRate(upper_limit_kwh=500, rate=0.12)


class FixedCharge(Component):
    name: str = ""
    amount: float = Field(..., gt=0, description="Amount of the fixed charge in $/month")
    description: Optional[str] = Field(None, description="Description of the fixed charge")

    @classmethod
    def example(cls) -> "FixedCharge":
        return FixedCharge(amount=15.00, description="Monthly fixed customer charge")


class DistributionTariff(Component):
    name: str = Field(..., description="Name of the tariff")
    utility: str = Field(..., description="Name of the utility company")
    customer_class: CustomerClass = Field(..., description="Customer class for the tariff")
    fixed_charge: FixedCharge = Field(..., description="Fixed charge for the tariff")
    seasonal_tou: List[SeasonalTOURates] = Field(
        ..., description="Seasonal TOU rates for the tariff"
    )
    demand_charges: Optional[List[DemandCharge]] = Field(
        None, description="List of demand charges for the tariff"
    )
    tiered_energy_charges: Optional[List[TieredRate]] = Field(
        None, description="List of tiered energy charges for the tariff"
    )

    @classmethod
    def example(cls) -> "DistributionTariff":
        return DistributionTariff(
            name="Residential Summer Tariff",
            utility="Example Utility",
            customer_class=CustomerClass.RESIDENTIAL,
            fixed_charge=FixedCharge.example(),
            seasonal_tou=[
                SeasonalTOURates.example(),
                SeasonalTOURates(
                    season=Season.WINTER,
                    tou_periods=[
                        TOURatePeriod.example(),
                        TOURatePeriod(
                            start_time=time(0, 0),
                            end_time=time(6, 0),
                            rate=0.10,
                            period_type=TOUPeriodType.OFF_PEAK,
                        ),
                    ],
                ),
            ],
            demand_charges=[DemandCharge.example()],
            tiered_energy_charges=[TieredRate.example()],
        )
