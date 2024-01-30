import importlib
import typing
import sqlite3
from types import NoneType
from typing import get_origin, get_args
import datetime
from enum import Enum

from loguru import logger
from infrasys.base_quantity import BaseQuantity

from gdm.cost.cost_models import BaseCost
from pydantic import BaseModel


ANNOTATION_TO_SQLITE_MAPPING = {
    int: "integer",
    str: "text",
    float: "real",
    bool: "integer",
    datetime.datetime: "text",
}


class QuantityModel(BaseModel):
    module_type: typing.Any
    class_name: str


class SQLiteCostDB:
    """Class managing SQlite interface for managing cost data."""

    def __init__(self, db_file: str):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def close(self):
        """Method to close the database connection."""
        self.conn.commit()
        self.conn.close()

    def __enter__(self):
        """Entry point for context manager."""
        return self

    def __exit__(self, *args, **kwargs):
        """Exit for context manager."""
        self.close()

    def _get_existing_tables(self):
        """Method to return all tables in database."""

        tables = self.cursor.execute("select name from sqlite_master")
        return [table[0] for table in tables]

    def _get_base_type(self, field_type: typing.Type):
        """Internal function to get base type from annotation."""

        if field_type in ANNOTATION_TO_SQLITE_MAPPING:
            return field_type

        elif get_origin(field_type) in [typing.Union, typing.Annotated]:
            args = get_args(field_type)

            if len(args) == 2 and NoneType in args:
                return self._get_base_type((set(args) - set([NoneType])).pop())

            # This logic is necessary for confloat, conint in pydantic models
            """ >>> class A(BaseModel):
                    a: Optional[confloat(gt=2)]

                >>> {'a': FieldInfo(annotation=Union[Annotated[float, NoneType, Interval,
                NoneType, NoneType], NoneType], required=True)}

                >>> get_args(A.model_fields['a'].annotation)
                (typing.Annotated[float, None, Interval(gt=2, ge=None, lt=None,
                le=None), None, None], <class 'NoneType'>)
            """
            not_none_args = set(args) - set([None])
            arg_types = [el for el in not_none_args if isinstance(el, type)]
            if len(not_none_args) == 2 and len(arg_types) == 1:
                return self._get_base_type(arg_types.pop())

            msg = f"Type error: {field_type=}"
            raise NotImplementedError(msg)

        elif issubclass(field_type, Enum) and issubclass(field_type, str):
            return str
        elif issubclass(field_type, BaseQuantity):
            return str
        else:
            msg = f"Type error {field_type=}"
            raise NotImplementedError(msg)

    def _create_table(self, cost_obj: BaseCost):
        """Method to create table for given cost type."""

        columns = []
        model_fields = cost_obj.model_fields
        if "id" not in model_fields:
            msg = f"id field is missing in {cost_obj=}"
            raise ValueError(msg)

        model_fields.pop("id")
        columns.append("id integer primary key autoincrement")

        for field, fieldinfo in model_fields.items():
            base_type = self._get_base_type(field_type=fieldinfo.annotation)
            columns.append(f"{field} {ANNOTATION_TO_SQLITE_MAPPING[base_type]}")

        table_name = cost_obj.__class__.__name__.lower()
        sql_query = f"create table {table_name}({','.join(columns)})"
        logger.info(f"Creating table: {sql_query=}")
        self.cursor.execute(sql_query)
        logger.info(f"Created table {table_name} successfully.")

    def add_cost(self, cost: BaseCost):
        """Method to add cost to database."""

        table_name = cost.__class__.__name__.lower()
        if table_name not in self._get_existing_tables():
            self._create_table(cost)
        cost_obj = cost.model_dump(mode="json")
        cost_obj.pop("id")

        columns = ", ".join(cost_obj.keys())
        placeholders = ", ".join(["?" for _ in cost_obj.values()])
        sql_query = f"insert into {table_name} ({columns}) values ({placeholders})"

        self.cursor.execute(sql_query, list(cost_obj.values()))

    def add_costs(self, costs: list[BaseCost]):
        """Method to add costs to database."""

        for cost in costs:
            self.add_cost(cost)

    def _get_quantity_model(self, field_type: typing.Type) -> QuantityModel | None:
        """Method to return quantity model."""
        if get_origin(field_type) in [typing.Union, typing.Annotated]:
            args = get_args(field_type)

            if len(args) == 2 and NoneType in args:
                return self._get_quantity_model((set(args) - set([NoneType])).pop())

        elif issubclass(field_type, BaseQuantity):
            return QuantityModel(
                module_type=importlib.import_module(field_type.__module__),
                class_name=field_type.__name__,
            )

    def _get_quantity_mapping(self, cost_type: typing.Type[BaseModel]) -> dict[str, QuantityModel]:
        """Internal method to get quantity model if present."""
        quantity_mapping: dict[str, QuantityModel] = {}
        for field, fieldinfo in cost_type.model_fields.items():
            q_model = self._get_quantity_model(fieldinfo.annotation)
            if q_model is not None:
                quantity_mapping[field] = q_model
        return quantity_mapping

    def _get_pydantic_obj(
        self,
        cost_type: typing.Type[BaseCost],
        data: dict,
        quantity_mapping: dict[str, QuantityModel],
    ):
        return cost_type(
            **{
                k: getattr(quantity_mapping[k].module_type, quantity_mapping[k].class_name)(
                    *self._split_qauntity_value(v)
                )
                if k in quantity_mapping
                else v
                for k, v in data.items()
            }
        )

    @staticmethod
    def _split_qauntity_value(value: str) -> (float, str):
        """Static method to split quantity values."""
        fields = value.split()
        if len(fields) != 2:
            msg = f"Length of split must be 2. {fields=}"
            raise ValueError(msg)

        return (float(fields[0]), fields[1])

    def get_cost(self, cost_type: BaseCost, id: int) -> BaseCost:
        """Method to return the cost component."""
        table_name = cost_type.__name__.lower()

        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in self.cursor.fetchall()]

        self.cursor.execute(f"SELECT * FROM {table_name} where id=?", (id,))
        rows = self.cursor.fetchall()[0]

        data = dict(zip(columns, rows))
        quantity_mapping = self._get_quantity_mapping(cost_type=cost_type)
        return self._get_pydantic_obj(cost_type, data, quantity_mapping)

    def get_costs(self, cost_type: BaseCost) -> list[BaseCost]:
        """Method to return the cost components"""
        table_name = cost_type.__name__.lower()

        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in self.cursor.fetchall()]

        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()

        quantity_mapping = self._get_quantity_mapping(cost_type=cost_type)
        return [
            self._get_pydantic_obj(cost_type, dict(zip(columns, row)), quantity_mapping)
            for row in rows
        ]
