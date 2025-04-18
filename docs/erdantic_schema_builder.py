"""This module contains class for auto documenting pydantic classes."""

# standard imports
import enum
import logging
from pathlib import Path

# third-party imports
import erdantic as erd
import gdm.distribution
import gdm.distribution.components
import gdm.distribution.controllers
import gdm.distribution.equipment
import gdm.distribution.model_reduction
from mdutils import Html
from mdutils.mdutils import MdUtils
from pydantic import BaseModel

# internal imports
import gdm

folder_path = Path(__file__).parent


class PydanticDocBuilder:
    """Builder class for automatically documenting pydantic classes."""

    def __init__(self, md_filename="models"):
        # asset_list =
        self.create_schema_diagrams(md_filename)
        # self.create_markdown_file(md_filename, asset_list)

    def create_schema_diagrams(self, md_filename):
        """Method to create schema diagrams."""
        asset_list = {}
        for mod in [
            gdm.distribution.common,
            gdm.distribution.components,
            gdm.distribution.equipment,
            gdm.distribution.controllers,
            gdm.distribution.model_reduction,
        ]:
            for asset in dir(mod):
                if not asset.startswith("_") and asset != "BaseModel":
                    model = getattr(mod, asset)
                    if isinstance(model, type):
                        print(model, issubclass(model, BaseModel))  # noqa: T201
                        if not issubclass(model, enum.Enum):
                            try:
                                file_fath = folder_path / md_filename / f"{asset}.svg"
                                diagram = erd.create(model)
                                diagram.draw(file_fath)
                                asset_list[asset] = f"{asset}.svg"
                            except Exception as e:
                                print(e)
                                logging.info(str(e))
        return asset_list

    def create_markdown_file(self, md_filename, asset_list):
        """Method to create markdown file."""
        md_file_path = folder_path / md_filename
        md_file = MdUtils(file_name=str(md_file_path))
        md_file.new_header(level=1, title="Library data models")
        md_file.new_paragraph(
            "This page provides details on the data models part of the GDM library."
        )

        md_file.new_paragraph()
        for asset_name, asset_schema_path in asset_list.items():
            md_file.new_paragraph(Html.image(path=asset_schema_path))
            md_file.write(" \n")
            md_file.write(f"::: gdm.{asset_name}\n")
            md_file.write(" \n")

        md_file.write(" \n")
        md_file.create_md_file()


PydanticDocBuilder()
