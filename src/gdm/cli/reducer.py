from pathlib import Path
import shutil
import click

from gdm.distribution.model_reduction.reducer import reduce_to_three_phase_system
from gdm.distribution.distribution_system import DistributionSystem
from gdm.exceptions import FolderAlreadyExistsError


@click.command()
@click.option(
    "-g",
    "--gdm-file",
    type=str,
    help="GDM system JSON file path.",
)
@click.option(
    "-t",
    "--target-file",
    type=str,
    help="Target GDM system JSON file path.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Force delete the target GDM system file if already exists.",
)
@click.option(
    "-r",
    "--reducer",
    type=click.Choice(["three_phase"]),
    help="Delete target GDM file forcefully if exists.",
)
@click.option(
    "-ts",
    "--time-series",
    is_flag=True,
    default=False,
    help="Delete target GDM file forcefully if exists.",
)
def reduce(gdm_file: str, target_file: str, force: bool, reducer: str, time_series: bool):
    target_file: Path = Path(target_file)
    if force and target_file.exists():
        shutil.rmtree(target_file.parent / f"{target_file.stem}_time_series")
        target_file.unlink()

    if not force and target_file.exists():
        raise FolderAlreadyExistsError(
            f"""{target_file} already exists. Consider
                                       deleting it first."""
        )
    sys = DistributionSystem.from_json(gdm_file)
    reducer_func = {"three_phase": reduce_to_three_phase_system}
    new_sys_name = sys.name + "_reduced" if sys.name else None
    new_sys = reducer_func[reducer](sys, new_sys_name, time_series)
    new_sys.to_json(target_file)
    click.echo(str(target_file))
