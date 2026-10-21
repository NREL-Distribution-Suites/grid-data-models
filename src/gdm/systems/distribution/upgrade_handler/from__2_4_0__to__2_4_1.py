from loguru import logger


def from__2_4_0__to__2_4_1(data: dict, from_version: str, to_version: str) -> dict:
    """Advance the version for optional generic equipment fields without changing existing data.

    This does not convert legacy DiTTo supplemental metadata; those models must be regenerated.
    """
    logger.info(f"Upgrading DistributionSystem from version {from_version} to {to_version}")
    data["data_format_version"] = str(to_version)
    return data
