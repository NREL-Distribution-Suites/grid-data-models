from loguru import logger


def from__2_4_0__to__2_5_0(data: dict, from_version: str, to_version: str) -> dict:
    """Advance the serialized data format to 2.5.0."""

    logger.info(f"Upgrading DistributionSystem from version {from_version} to {to_version}")
    data["data_format_version"] = str(to_version)
    return data
