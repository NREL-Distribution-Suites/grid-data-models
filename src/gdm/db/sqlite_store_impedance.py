"""Shared impedance matrix helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3


def _insert_impedance_matrix_entries(
    conn: sqlite3.Connection,
    equipment_id: int,
    equipment_type: str,
    matrix_type: str,
    matrix_values,
    value_unit: str,
) -> None:
    for row_idx, row_values in enumerate(matrix_values):
        for col_idx, value in enumerate(row_values):
            conn.execute(
                """
                INSERT INTO impedance_matrix_entries(
                    equipment_id,
                    equipment_type,
                    matrix_type,
                    row_idx,
                    col_idx,
                    value,
                    value_unit
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    equipment_id,
                    equipment_type,
                    matrix_type,
                    row_idx,
                    col_idx,
                    float(value),
                    value_unit,
                ),
            )


def _load_impedance_matrix(
    conn: sqlite3.Connection,
    equipment_id: int,
    equipment_type: str,
    matrix_type: str,
) -> tuple[list[list[float]], str]:
    rows = conn.execute(
        """
        SELECT row_idx, col_idx, value, value_unit
        FROM impedance_matrix_entries
        WHERE equipment_id = ? AND equipment_type = ? AND matrix_type = ?
        ORDER BY row_idx, col_idx
        """,
        (equipment_id, equipment_type, matrix_type),
    ).fetchall()
    if not rows:
        raise ValueError(
            f"Missing impedance matrix entries for equipment_id={equipment_id}, equipment_type={equipment_type}, matrix_type={matrix_type}"
        )

    size = max(max(row_idx, col_idx) for row_idx, col_idx, _, _ in rows) + 1
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    unit = rows[0][3]
    for row_idx, col_idx, value, _ in rows:
        matrix[row_idx][col_idx] = value

    return matrix, unit
