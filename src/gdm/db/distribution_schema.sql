-- DISCLAIMER
-- The current version of this schema only works for SQLITE >=3.45
-- When adding new functionality, think about the following:
--      1. Simplicity and ease of use over complexity,
--      2. Clear, concise and strict fields but allow for extensability,
--      3. User friendly over performance, but consider performance always.
-- WARNING: This script should only be used while testing the schema and should
-- not be applied to existing datasets since it drops all existing information.
--
-- DESIGN NOTES
-- * Every field from every pydantic model is represented as a native column.
-- * No JSON columns are used. All arrays and nested objects are normalized
--   into dedicated tables linked by foreign keys.
-- * Physical quantities are stored as a REAL value + TEXT unit column pair.
-- * Ordered arrays (phases, tap positions, matrix rows, curve points, etc.)
--   include a position_index INTEGER to preserve ordering.
-- * Polymorphic controller types use a type_discriminator TEXT column with a
--   CHECK constraint listing the allowed subtypes. Subtype-specific fields are
--   nullable and only populated for the relevant subtype.
-- * Component tables mirror the Python pydantic model hierarchy:
--     Topology  : feeders -> substations -> buses
--     Equipment : wire/cable catalogs -> branch/transformer/load equipment
--     Components: loads, branches, transformers, DERs, switchgear
-- -----------------------------------------------------------------------------

-- ============================================================
-- DROP TABLES  (most-dependent first)
-- ============================================================
DROP TABLE IF EXISTS time_series_associations;
DROP TABLE IF EXISTS regulator_winding_phases;
DROP TABLE IF EXISTS regulator_winding_buses;
DROP TABLE IF EXISTS regulator_controllers;
DROP TABLE IF EXISTS distribution_regulators;
DROP TABLE IF EXISTS transformer_winding_phases;
DROP TABLE IF EXISTS transformer_winding_buses;
DROP TABLE IF EXISTS distribution_transformers;
DROP TABLE IF EXISTS switch_phase_states;
DROP TABLE IF EXISTS matrix_impedance_switch_phases;
DROP TABLE IF EXISTS matrix_impedance_switches;
DROP TABLE IF EXISTS recloser_phase_states;
DROP TABLE IF EXISTS matrix_impedance_recloser_phases;
DROP TABLE IF EXISTS matrix_impedance_reclosers;
DROP TABLE IF EXISTS recloser_reclose_intervals;
DROP TABLE IF EXISTS recloser_controllers;
DROP TABLE IF EXISTS fuse_phase_states;
DROP TABLE IF EXISTS matrix_impedance_fuse_phases;
DROP TABLE IF EXISTS matrix_impedance_fuses;
DROP TABLE IF EXISTS geometry_branch_thermal_limits;
DROP TABLE IF EXISTS geometry_branch_phases;
DROP TABLE IF EXISTS geometry_branches;
DROP TABLE IF EXISTS sequence_impedance_branch_thermal_limits;
DROP TABLE IF EXISTS sequence_impedance_branch_phases;
DROP TABLE IF EXISTS sequence_impedance_branches;
DROP TABLE IF EXISTS matrix_impedance_branch_thermal_limits;
DROP TABLE IF EXISTS matrix_impedance_branch_phases;
DROP TABLE IF EXISTS matrix_impedance_branches;
DROP TABLE IF EXISTS distribution_voltage_source_phases;
DROP TABLE IF EXISTS distribution_voltage_sources;
DROP TABLE IF EXISTS distribution_capacitor_phases;
DROP TABLE IF EXISTS capacitor_controllers;
DROP TABLE IF EXISTS distribution_capacitors;
DROP TABLE IF EXISTS distribution_battery_phases;
DROP TABLE IF EXISTS distribution_batteries;
DROP TABLE IF EXISTS distribution_solar_phases;
DROP TABLE IF EXISTS distribution_solar;
DROP TABLE IF EXISTS distribution_load_phases;
DROP TABLE IF EXISTS distribution_loads;
DROP TABLE IF EXISTS inverter_controllers;
DROP TABLE IF EXISTS inverter_active_power_controls;
DROP TABLE IF EXISTS inverter_reactive_power_controls;
DROP TABLE IF EXISTS bus_voltage_limits;
DROP TABLE IF EXISTS bus_phases;
DROP TABLE IF EXISTS distribution_buses;
DROP TABLE IF EXISTS substation_feeders;
DROP TABLE IF EXISTS distribution_substations;
DROP TABLE IF EXISTS distribution_feeders;
DROP TABLE IF EXISTS thermal_limit_sets;
DROP TABLE IF EXISTS voltage_limit_sets;
DROP TABLE IF EXISTS voltage_source_phases;
DROP TABLE IF EXISTS voltage_source_equipment;
DROP TABLE IF EXISTS phase_voltage_source_equipment;
DROP TABLE IF EXISTS inverter_equipment;
DROP TABLE IF EXISTS battery_equipment;
DROP TABLE IF EXISTS solar_equipment;
DROP TABLE IF EXISTS capacitor_equipment_phases;
DROP TABLE IF EXISTS capacitor_equipment;
DROP TABLE IF EXISTS phase_capacitor_equipment;
DROP TABLE IF EXISTS load_equipment_phases;
DROP TABLE IF EXISTS load_equipment;
DROP TABLE IF EXISTS phase_load_equipment;
DROP TABLE IF EXISTS winding_tap_positions;
DROP TABLE IF EXISTS transformer_coupling_sequences;
DROP TABLE IF EXISTS winding_equipment;
DROP TABLE IF EXISTS distribution_transformer_equipment;
DROP TABLE IF EXISTS impedance_matrix_entries;
DROP TABLE IF EXISTS matrix_impedance_switch_equipment;
DROP TABLE IF EXISTS switch_controllers;
DROP TABLE IF EXISTS recloser_controller_equipment;
DROP TABLE IF EXISTS matrix_impedance_recloser_equipment;
DROP TABLE IF EXISTS matrix_impedance_fuse_equipment;
DROP TABLE IF EXISTS matrix_impedance_branch_equipment;
DROP TABLE IF EXISTS sequence_impedance_branch_equipment;
DROP TABLE IF EXISTS geometry_branch_conductors;
DROP TABLE IF EXISTS geometry_branch_equipment;
DROP TABLE IF EXISTS concentric_cable_equipment;
DROP TABLE IF EXISTS bare_conductor_equipment;
DROP TABLE IF EXISTS time_current_curve_points;
DROP TABLE IF EXISTS time_current_curves;
DROP TABLE IF EXISTS curve_points;
DROP TABLE IF EXISTS curves;
DROP TABLE IF EXISTS wire_insulation_types;
DROP TABLE IF EXISTS line_types;
DROP TABLE IF EXISTS transformer_mountings;
DROP TABLE IF EXISTS connection_types;
DROP TABLE IF EXISTS voltage_types;
DROP TABLE IF EXISTS limit_types;
DROP TABLE IF EXISTS phases;

PRAGMA foreign_keys = ON;

-- ============================================================
-- REFERENCE / ENUM TABLES
-- ============================================================

CREATE TABLE phases (name TEXT PRIMARY KEY);
INSERT INTO phases VALUES ('A'), ('B'), ('C'), ('N'), ('S1'), ('S2');

CREATE TABLE voltage_types (name TEXT PRIMARY KEY);
INSERT INTO voltage_types VALUES ('line-to-line'), ('line-to-ground');

CREATE TABLE connection_types (name TEXT PRIMARY KEY);
INSERT INTO connection_types VALUES
    ('STAR'), ('DELTA'), ('OPEN_DELTA'), ('OPEN_STAR'), ('ZIG_ZAG');

CREATE TABLE limit_types (name TEXT PRIMARY KEY);
INSERT INTO limit_types VALUES ('min'), ('max');

CREATE TABLE transformer_mountings (name TEXT PRIMARY KEY);
INSERT INTO transformer_mountings VALUES
    ('POLE_MOUNT'), ('PAD_MOUNT'), ('UNDERGROUND_VAULT');

CREATE TABLE line_types (name TEXT PRIMARY KEY);
INSERT INTO line_types VALUES ('OVERHEAD'), ('UNDERGROUND');

-- Relative permittivity values for wire insulation materials.
CREATE TABLE wire_insulation_types (
    name        TEXT PRIMARY KEY,
    dielectric  REAL NOT NULL
);
INSERT INTO wire_insulation_types VALUES
    ('AIR', 1.0), ('PVC', 3.18), ('XLPE', 2.3), ('EPR', 2.5),
    ('PE', 2.25), ('TEFLON', 2.1), ('SILICONE_RUBBER', 3.5),
    ('PAPER', 3.7), ('MICA', 6.0);

-- ============================================================
-- CURVE TABLES
-- ============================================================

-- Generic (x, y) curve -- used for volt-var, volt-watt, PV power-temp,
-- and inverter efficiency curves.
CREATE TABLE curves (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL DEFAULT ''
);

-- Ordered breakpoints for a Curve.
CREATE TABLE curve_points (
    id              INTEGER PRIMARY KEY,
    curve_id        INTEGER NOT NULL REFERENCES curves (id) ON DELETE CASCADE,
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    x_value         REAL    NOT NULL,
    y_value         REAL    NOT NULL,
    UNIQUE (curve_id, position_index)
);

-- Time-current curve header -- used for fuse and recloser TCC protection curves.
CREATE TABLE time_current_curves (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL DEFAULT ''
);

-- Ordered breakpoints for a TimeCurrentCurve.
CREATE TABLE time_current_curve_points (
    id              INTEGER PRIMARY KEY,
    curve_id        INTEGER NOT NULL REFERENCES time_current_curves (id) ON DELETE CASCADE,
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    current_value   REAL    NOT NULL CHECK (current_value >= 0),
    current_unit    TEXT    NOT NULL DEFAULT 'ampere',
    time_value      REAL    NOT NULL CHECK (time_value >= 0),
    time_unit       TEXT    NOT NULL DEFAULT 'second',
    UNIQUE (curve_id, position_index)
);

-- ============================================================
-- WIRE / CABLE CATALOG
-- ============================================================

-- Bare conductor (overhead wire) catalog entry.
CREATE TABLE bare_conductor_equipment (
    id                      INTEGER PRIMARY KEY,
    name                    TEXT    NOT NULL UNIQUE,
    conductor_diameter      REAL    NOT NULL CHECK (conductor_diameter > 0),
    conductor_diameter_unit TEXT    NOT NULL DEFAULT 'meter',
    conductor_gmr           REAL    NOT NULL CHECK (conductor_gmr > 0),
    conductor_gmr_unit      TEXT    NOT NULL DEFAULT 'meter',
    ampacity                REAL    NOT NULL CHECK (ampacity > 0),
    ampacity_unit           TEXT    NOT NULL DEFAULT 'ampere',
    emergency_ampacity      REAL    NOT NULL CHECK (emergency_ampacity > 0),
    emergency_ampacity_unit TEXT    NOT NULL DEFAULT 'ampere',
    ac_resistance           REAL    NOT NULL CHECK (ac_resistance > 0),
    ac_resistance_unit      TEXT    NOT NULL DEFAULT 'ohm/meter',
    dc_resistance           REAL    NOT NULL CHECK (dc_resistance > 0),
    dc_resistance_unit      TEXT    NOT NULL DEFAULT 'ohm/meter'
);

-- Concentric (underground) cable catalog entry.
CREATE TABLE concentric_cable_equipment (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL UNIQUE,
    strand_diameter             REAL    NOT NULL CHECK (strand_diameter > 0),
    strand_diameter_unit        TEXT    NOT NULL DEFAULT 'meter',
    conductor_diameter          REAL    NOT NULL CHECK (conductor_diameter > 0),
    conductor_diameter_unit     TEXT    NOT NULL DEFAULT 'meter',
    cable_diameter              REAL    NOT NULL CHECK (cable_diameter > 0),
    cable_diameter_unit         TEXT    NOT NULL DEFAULT 'meter',
    insulation_thickness        REAL    NOT NULL CHECK (insulation_thickness > 0),
    insulation_thickness_unit   TEXT    NOT NULL DEFAULT 'meter',
    insulation_diameter         REAL    NOT NULL CHECK (insulation_diameter > 0),
    insulation_diameter_unit    TEXT    NOT NULL DEFAULT 'meter',
    ampacity                    REAL    NOT NULL CHECK (ampacity > 0),
    ampacity_unit               TEXT    NOT NULL DEFAULT 'ampere',
    conductor_gmr               REAL    NOT NULL CHECK (conductor_gmr > 0),
    conductor_gmr_unit          TEXT    NOT NULL DEFAULT 'meter',
    strand_gmr                  REAL    NOT NULL CHECK (strand_gmr > 0),
    strand_gmr_unit             TEXT    NOT NULL DEFAULT 'meter',
    phase_ac_resistance         REAL    NOT NULL CHECK (phase_ac_resistance > 0),
    phase_ac_resistance_unit    TEXT    NOT NULL DEFAULT 'ohm/meter',
    strand_ac_resistance        REAL    NOT NULL CHECK (strand_ac_resistance > 0),
    strand_ac_resistance_unit   TEXT    NOT NULL DEFAULT 'ohm/meter',
    num_neutral_strands         INTEGER NOT NULL CHECK (num_neutral_strands > 0),
    rated_voltage               REAL    NOT NULL CHECK (rated_voltage > 0),
    rated_voltage_unit          TEXT    NOT NULL DEFAULT 'volt',
    insulation                  TEXT    NOT NULL DEFAULT 'PE'
        REFERENCES wire_insulation_types (name)
);

-- ============================================================
-- BRANCH EQUIPMENT
-- ============================================================

-- Sequence impedance branch equipment.
CREATE TABLE sequence_impedance_branch_equipment (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL UNIQUE,
    pos_seq_resistance          REAL    NOT NULL,
    pos_seq_resistance_unit     TEXT    NOT NULL DEFAULT 'ohm/meter',
    zero_seq_resistance         REAL    NOT NULL,
    zero_seq_resistance_unit    TEXT    NOT NULL DEFAULT 'ohm/meter',
    pos_seq_reactance           REAL    NOT NULL,
    pos_seq_reactance_unit      TEXT    NOT NULL DEFAULT 'ohm/meter',
    zero_seq_reactance          REAL    NOT NULL,
    zero_seq_reactance_unit     TEXT    NOT NULL DEFAULT 'ohm/meter',
    pos_seq_capacitance         REAL    NOT NULL,
    pos_seq_capacitance_unit    TEXT    NOT NULL DEFAULT 'farad/meter',
    zero_seq_capacitance        REAL    NOT NULL,
    zero_seq_capacitance_unit   TEXT    NOT NULL DEFAULT 'farad/meter',
    ampacity                    REAL    NOT NULL CHECK (ampacity > 0),
    ampacity_unit               TEXT    NOT NULL DEFAULT 'ampere'
);

-- Matrix impedance branch equipment header.
-- The N*N R/X/C matrices are stored row-by-row in impedance_matrix_entries.
CREATE TABLE matrix_impedance_branch_equipment (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    construction    TEXT    NOT NULL DEFAULT 'OVERHEAD' REFERENCES line_types (name),
    ampacity        REAL    NOT NULL CHECK (ampacity > 0),
    ampacity_unit   TEXT    NOT NULL DEFAULT 'ampere'
);

-- Shared N*N impedance matrix storage for line, fuse, recloser, and switch equipment.
-- equipment_type IN ('LINE','FUSE','RECLOSER','SWITCH') identifies the parent table.
-- matrix_type IN ('R','X','C') identifies resistance, reactance, or capacitance.
-- Cross-table FK enforcement is the responsibility of the application layer.
CREATE TABLE impedance_matrix_entries (
    id              INTEGER PRIMARY KEY,
    equipment_id    INTEGER NOT NULL,
    equipment_type  TEXT    NOT NULL CHECK (equipment_type IN ('LINE','FUSE','RECLOSER','SWITCH')),
    matrix_type     TEXT    NOT NULL CHECK (matrix_type IN ('R','X','C')),
    row_idx         INTEGER NOT NULL CHECK (row_idx >= 0),
    col_idx         INTEGER NOT NULL CHECK (col_idx >= 0),
    value           REAL    NOT NULL,
    value_unit      TEXT    NOT NULL,
    UNIQUE (equipment_id, equipment_type, matrix_type, row_idx, col_idx)
);

-- Fuse equipment: matrix impedance + TCC curve + trip delay.
CREATE TABLE matrix_impedance_fuse_equipment (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    construction    TEXT    NOT NULL DEFAULT 'OVERHEAD' REFERENCES line_types (name),
    ampacity        REAL    NOT NULL CHECK (ampacity > 0),
    ampacity_unit   TEXT    NOT NULL DEFAULT 'ampere',
    delay           REAL    NOT NULL DEFAULT 0.0 CHECK (delay >= 0),
    delay_unit      TEXT    NOT NULL DEFAULT 'second',
    tcc_curve_id    INTEGER NOT NULL REFERENCES time_current_curves (id) ON DELETE RESTRICT
);

-- Recloser controller equipment: physical relay model identified by name.
CREATE TABLE recloser_controller_equipment (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL UNIQUE
);

-- Recloser equipment: matrix impedance, protection logic is in recloser_controllers.
CREATE TABLE matrix_impedance_recloser_equipment (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    construction    TEXT    NOT NULL DEFAULT 'OVERHEAD' REFERENCES line_types (name),
    ampacity        REAL    NOT NULL CHECK (ampacity > 0),
    ampacity_unit   TEXT    NOT NULL DEFAULT 'ampere'
);

-- Switch controller: delay, normal state, and lock flag.
CREATE TABLE switch_controllers (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL DEFAULT '',
    delay           REAL    NOT NULL CHECK (delay >= 0),
    delay_unit      TEXT    NOT NULL DEFAULT 'second',
    normal_state    TEXT    NOT NULL CHECK (normal_state IN ('open', 'close')),
    is_locked       INTEGER NOT NULL DEFAULT 0 CHECK (is_locked IN (0, 1))
);

-- Switch equipment: matrix impedance + optional switch controller.
CREATE TABLE matrix_impedance_switch_equipment (
    id                      INTEGER PRIMARY KEY,
    name                    TEXT    NOT NULL UNIQUE,
    construction            TEXT    NOT NULL DEFAULT 'OVERHEAD' REFERENCES line_types (name),
    ampacity                REAL    NOT NULL CHECK (ampacity > 0),
    ampacity_unit           TEXT    NOT NULL DEFAULT 'ampere',
    switch_controller_id    INTEGER NULL
        REFERENCES switch_controllers (id) ON DELETE SET NULL
);

-- Geometry branch equipment header.
-- Conductor positions are stored in geometry_branch_conductors (one row per conductor).
CREATE TABLE geometry_branch_equipment (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL UNIQUE,
    insulation  TEXT    NOT NULL DEFAULT 'AIR' REFERENCES wire_insulation_types (name)
);

-- Each row is one conductor slot in a geometry branch.
-- Exactly one of bare_conductor_id / concentric_cable_id must be set.
-- horizontal_position and vertical_position replace the former JSON position arrays.
CREATE TABLE geometry_branch_conductors (
    id                          INTEGER PRIMARY KEY,
    equipment_id                INTEGER NOT NULL
        REFERENCES geometry_branch_equipment (id) ON DELETE CASCADE,
    position_index              INTEGER NOT NULL CHECK (position_index >= 0),
    horizontal_position         REAL    NOT NULL,
    horizontal_position_unit    TEXT    NOT NULL DEFAULT 'meter',
    vertical_position           REAL    NOT NULL,
    vertical_position_unit      TEXT    NOT NULL DEFAULT 'meter',
    bare_conductor_id           INTEGER NULL
        REFERENCES bare_conductor_equipment (id) ON DELETE SET NULL,
    concentric_cable_id         INTEGER NULL
        REFERENCES concentric_cable_equipment (id) ON DELETE SET NULL,
    CHECK ((bare_conductor_id IS NOT NULL) != (concentric_cable_id IS NOT NULL)),
    UNIQUE (equipment_id, position_index)
);

-- ============================================================
-- TRANSFORMER EQUIPMENT
-- ============================================================

-- Distribution transformer / regulator equipment catalog header.
CREATE TABLE distribution_transformer_equipment (
    id                  INTEGER PRIMARY KEY,
    name                TEXT    NOT NULL UNIQUE,
    mounting            TEXT    NOT NULL DEFAULT 'POLE_MOUNT'
        REFERENCES transformer_mountings (name),
    pct_no_load_loss    REAL    NOT NULL
        CHECK (pct_no_load_loss  >= 0 AND pct_no_load_loss  <= 100),
    pct_full_load_loss  REAL    NOT NULL
        CHECK (pct_full_load_loss >= 0 AND pct_full_load_loss <= 100),
    is_center_tapped    INTEGER NOT NULL CHECK (is_center_tapped IN (0, 1))
);

-- Individual winding. Ordered tap_positions stored in winding_tap_positions.
CREATE TABLE winding_equipment (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL DEFAULT '',
    transformer_equipment_id    INTEGER NOT NULL
        REFERENCES distribution_transformer_equipment (id) ON DELETE CASCADE,
    winding_index               INTEGER NOT NULL CHECK (winding_index >= 0),
    resistance                  REAL    NOT NULL
        CHECK (resistance >= 0 AND resistance <= 100),
    is_grounded                 INTEGER NOT NULL CHECK (is_grounded IN (0, 1)),
    rated_voltage               REAL    NOT NULL CHECK (rated_voltage > 0),
    rated_voltage_unit          TEXT    NOT NULL DEFAULT 'volt',
    voltage_type                TEXT    NOT NULL REFERENCES voltage_types (name),
    rated_power                 REAL    NOT NULL CHECK (rated_power > 0),
    rated_power_unit            TEXT    NOT NULL DEFAULT 'volt_ampere',
    num_phases                  INTEGER NOT NULL CHECK (num_phases >= 1 AND num_phases <= 3),
    connection_type             TEXT    NOT NULL REFERENCES connection_types (name),
    total_taps                  INTEGER NOT NULL DEFAULT 32,
    min_tap_pu                  REAL    NOT NULL DEFAULT 0.9
        CHECK (min_tap_pu >= 0 AND min_tap_pu <= 1.0),
    max_tap_pu                  REAL    NOT NULL DEFAULT 1.1 CHECK (max_tap_pu >= 1.0),
    UNIQUE (transformer_equipment_id, winding_index)
);

-- Per-phase tap position for a winding (replaces tap_positions JSON array).
CREATE TABLE winding_tap_positions (
    id              INTEGER PRIMARY KEY,
    winding_id      INTEGER NOT NULL REFERENCES winding_equipment (id) ON DELETE CASCADE,
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    tap_value       REAL    NOT NULL,
    UNIQUE (winding_id, position_index)
);

-- Winding-pair coupling record.
-- Merges coupling_sequences and winding_reactances JSON arrays into one table.
CREATE TABLE transformer_coupling_sequences (
    id                          INTEGER PRIMARY KEY,
    transformer_equipment_id    INTEGER NOT NULL
        REFERENCES distribution_transformer_equipment (id) ON DELETE CASCADE,
    sequence_index              INTEGER NOT NULL CHECK (sequence_index >= 0),
    from_winding_index          INTEGER NOT NULL CHECK (from_winding_index >= 0),
    to_winding_index            INTEGER NOT NULL CHECK (to_winding_index >= 0),
    reactance                   REAL    NOT NULL CHECK (reactance >= 0 AND reactance <= 100),
    reactance_unit              TEXT    NOT NULL DEFAULT 'percent',
    UNIQUE (transformer_equipment_id, sequence_index)
);

-- ============================================================
-- LOAD EQUIPMENT
-- ============================================================

-- Single-phase load (ZIP model).
CREATE TABLE phase_load_equipment (
    id                  INTEGER PRIMARY KEY,
    name                TEXT    NOT NULL UNIQUE,
    real_power          REAL    NOT NULL DEFAULT 0.0 CHECK (real_power >= 0),
    real_power_unit     TEXT    NOT NULL DEFAULT 'kilowatt',
    reactive_power      REAL    NOT NULL DEFAULT 0.0,
    reactive_power_unit TEXT    NOT NULL DEFAULT 'kilovar',
    z_real              REAL    NOT NULL,
    z_imag              REAL    NOT NULL,
    i_real              REAL    NOT NULL,
    i_imag              REAL    NOT NULL,
    p_real              REAL    NOT NULL,
    p_imag              REAL    NOT NULL,
    num_customers       INTEGER NULL CHECK (num_customers > 0)
);

-- Multi-phase load equipment header.
CREATE TABLE load_equipment (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    connection_type TEXT    NOT NULL DEFAULT 'STAR' REFERENCES connection_types (name)
);

-- Ordered per-phase load list (replaces phase_load_ids JSON array).
CREATE TABLE load_equipment_phases (
    id                      INTEGER PRIMARY KEY,
    load_equipment_id       INTEGER NOT NULL REFERENCES load_equipment      (id) ON DELETE CASCADE,
    phase_load_equipment_id INTEGER NOT NULL REFERENCES phase_load_equipment (id) ON DELETE RESTRICT,
    position_index          INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (load_equipment_id, position_index)
);

-- ============================================================
-- CAPACITOR EQUIPMENT
-- ============================================================

-- Single-phase capacitor bank.
CREATE TABLE phase_capacitor_equipment (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL UNIQUE,
    resistance                  REAL    NOT NULL DEFAULT 0.0 CHECK (resistance >= 0),
    resistance_unit             TEXT    NOT NULL DEFAULT 'ohm',
    reactance                   REAL    NOT NULL DEFAULT 0.0 CHECK (reactance  >= 0),
    reactance_unit              TEXT    NOT NULL DEFAULT 'ohm',
    rated_reactive_power        REAL    NOT NULL CHECK (rated_reactive_power > 0),
    rated_reactive_power_unit   TEXT    NOT NULL DEFAULT 'var',
    num_banks_on                INTEGER NOT NULL CHECK (num_banks_on >= 0),
    num_banks                   INTEGER NOT NULL DEFAULT 1 CHECK (num_banks > 0)
);

-- Multi-phase capacitor equipment header.
CREATE TABLE capacitor_equipment (
    id                  INTEGER PRIMARY KEY,
    name                TEXT    NOT NULL UNIQUE,
    connection_type     TEXT    NOT NULL DEFAULT 'STAR' REFERENCES connection_types (name),
    rated_voltage       REAL    NOT NULL CHECK (rated_voltage > 0),
    rated_voltage_unit  TEXT    NOT NULL DEFAULT 'volt',
    voltage_type        TEXT    NOT NULL REFERENCES voltage_types (name)
);

-- Ordered per-phase capacitor list (replaces phase_capacitor_ids JSON array).
CREATE TABLE capacitor_equipment_phases (
    id                           INTEGER PRIMARY KEY,
    capacitor_equipment_id       INTEGER NOT NULL
        REFERENCES capacitor_equipment      (id) ON DELETE CASCADE,
    phase_capacitor_equipment_id INTEGER NOT NULL
        REFERENCES phase_capacitor_equipment (id) ON DELETE RESTRICT,
    position_index               INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (capacitor_equipment_id, position_index)
);

-- ============================================================
-- SOLAR / BATTERY / INVERTER EQUIPMENT
-- ============================================================

-- PV array equipment.
-- power_temp_curve_id replaces the former power_temp_curve JSON column.
CREATE TABLE solar_equipment (
    id                    INTEGER PRIMARY KEY,
    name                  TEXT    NOT NULL UNIQUE,
    rated_power           REAL    NOT NULL CHECK (rated_power > 0),
    rated_power_unit      TEXT    NOT NULL DEFAULT 'kilowatt',
    power_temp_curve_id   INTEGER NULL REFERENCES curves (id) ON DELETE SET NULL,
    resistance            REAL    NOT NULL CHECK (resistance >= 0 AND resistance <= 100),
    reactance             REAL    NOT NULL CHECK (reactance  >= 0 AND reactance  <= 100),
    rated_voltage         REAL    NOT NULL CHECK (rated_voltage > 0),
    rated_voltage_unit    TEXT    NOT NULL DEFAULT 'volt',
    voltage_type          TEXT    NOT NULL REFERENCES voltage_types (name)
);

-- Battery (DC) equipment.
CREATE TABLE battery_equipment (
    id                      INTEGER PRIMARY KEY,
    name                    TEXT    NOT NULL UNIQUE,
    rated_energy            REAL    NOT NULL CHECK (rated_energy > 0),
    rated_energy_unit       TEXT    NOT NULL DEFAULT 'kilowatt_hour',
    rated_power             REAL    NOT NULL CHECK (rated_power >= 0),
    rated_power_unit        TEXT    NOT NULL DEFAULT 'kilowatt',
    charging_efficiency     REAL    NOT NULL
        CHECK (charging_efficiency >= 0 AND charging_efficiency <= 100),
    discharging_efficiency  REAL    NOT NULL
        CHECK (discharging_efficiency >= 0 AND discharging_efficiency <= 100),
    idling_efficiency       REAL    NOT NULL
        CHECK (idling_efficiency >= 0 AND idling_efficiency <= 100),
    rated_voltage           REAL    NOT NULL CHECK (rated_voltage >= 0),
    rated_voltage_unit      TEXT    NOT NULL DEFAULT 'volt',
    voltage_type            TEXT    NOT NULL REFERENCES voltage_types (name)
);

-- Inverter equipment.
-- eff_curve_id replaces the former eff_curve JSON column.
CREATE TABLE inverter_equipment (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL DEFAULT '',
    rated_apparent_power        REAL    NOT NULL CHECK (rated_apparent_power > 0),
    rated_apparent_power_unit   TEXT    NOT NULL DEFAULT 'volt_ampere',
    rise_limit                  REAL    NULL CHECK (rise_limit > 0),
    rise_limit_unit             TEXT    NULL DEFAULT 'watt/second',
    fall_limit                  REAL    NULL CHECK (fall_limit > 0),
    fall_limit_unit             TEXT    NULL DEFAULT 'watt/second',
    cutout_percent              REAL    NOT NULL CHECK (cutout_percent >= 0 AND cutout_percent <= 100),
    cutin_percent               REAL    NOT NULL CHECK (cutin_percent  >= 0 AND cutin_percent  <= 100),
    dc_to_ac_efficiency         REAL    NOT NULL
        CHECK (dc_to_ac_efficiency >= 0 AND dc_to_ac_efficiency <= 100),
    eff_curve_id                INTEGER NULL REFERENCES curves (id) ON DELETE SET NULL
);

-- ============================================================
-- VOLTAGE SOURCE EQUIPMENT
-- ============================================================

-- Single-phase Thevenin voltage source.
CREATE TABLE phase_voltage_source_equipment (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    r0              REAL    NOT NULL,   r0_unit  TEXT NOT NULL DEFAULT 'ohm',
    r1              REAL    NOT NULL,   r1_unit  TEXT NOT NULL DEFAULT 'ohm',
    x0              REAL    NOT NULL,   x0_unit  TEXT NOT NULL DEFAULT 'ohm',
    x1              REAL    NOT NULL,   x1_unit  TEXT NOT NULL DEFAULT 'ohm',
    voltage         REAL    NOT NULL CHECK (voltage > 0),
    voltage_unit    TEXT    NOT NULL DEFAULT 'volt',
    voltage_type    TEXT    NOT NULL DEFAULT 'line-to-line' REFERENCES voltage_types (name),
    angle           REAL    NOT NULL,
    angle_unit      TEXT    NOT NULL DEFAULT 'degree'
);

-- Three-phase voltage source header.
CREATE TABLE voltage_source_equipment (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL UNIQUE
);

-- Ordered list of per-phase sources (replaces source_ids JSON array).
CREATE TABLE voltage_source_phases (
    id                              INTEGER PRIMARY KEY,
    voltage_source_equipment_id     INTEGER NOT NULL
        REFERENCES voltage_source_equipment         (id) ON DELETE CASCADE,
    phase_source_equipment_id       INTEGER NOT NULL
        REFERENCES phase_voltage_source_equipment   (id) ON DELETE RESTRICT,
    position_index                  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (voltage_source_equipment_id, position_index)
);

-- ============================================================
-- LIMIT SETS
-- ============================================================

CREATE TABLE voltage_limit_sets (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL DEFAULT '',
    limit_type  TEXT    NOT NULL REFERENCES limit_types (name),
    value       REAL    NOT NULL CHECK (value > 0),
    value_unit  TEXT    NOT NULL DEFAULT 'volt'
);

CREATE TABLE thermal_limit_sets (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL DEFAULT '',
    limit_type  TEXT    NOT NULL REFERENCES limit_types (name),
    value       REAL    NOT NULL CHECK (value > 0),
    value_unit  TEXT    NOT NULL DEFAULT 'ampere'
);

-- ============================================================
-- TOPOLOGY
-- ============================================================

CREATE TABLE distribution_feeders (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL UNIQUE
);

CREATE TABLE distribution_substations (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL UNIQUE
);

-- Junction: feeders belonging to a substation.
CREATE TABLE substation_feeders (
    substation_id   INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    PRIMARY KEY (substation_id, feeder_id)
);

-- Bus: fundamental node of the distribution network.
-- coordinate_x / coordinate_y replace the former coordinate JSON column.
-- Phases are stored in bus_phases.
CREATE TABLE distribution_buses (
    id                  INTEGER PRIMARY KEY,
    name                TEXT    NOT NULL UNIQUE,
    substation_id       INTEGER NOT NULL
        REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id           INTEGER NOT NULL
        REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    voltage_type        TEXT    NOT NULL REFERENCES voltage_types (name),
    rated_voltage       REAL    NOT NULL CHECK (rated_voltage > 0),
    rated_voltage_unit  TEXT    NOT NULL DEFAULT 'volt',
    coordinate_x        REAL    NULL,
    coordinate_y        REAL    NULL,
    in_service          INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);

-- Ordered phase list for a bus (replaces phases JSON array).
CREATE TABLE bus_phases (
    id              INTEGER PRIMARY KEY,
    bus_id          INTEGER NOT NULL REFERENCES distribution_buses (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (bus_id, position_index),
    UNIQUE (bus_id, phase)
);

-- Voltage limit sets associated with a bus.
CREATE TABLE bus_voltage_limits (
    bus_id          INTEGER NOT NULL REFERENCES distribution_buses (id) ON DELETE CASCADE,
    limit_set_id    INTEGER NOT NULL REFERENCES voltage_limit_sets (id) ON DELETE CASCADE,
    PRIMARY KEY (bus_id, limit_set_id)
);

-- ============================================================
-- INVERTER CONTROLLER TABLES
-- ============================================================

-- Reactive power control setting for an inverter.
-- controller_type discriminates between POWER_FACTOR and VOLT_VAR subtypes.
CREATE TABLE inverter_reactive_power_controls (
    id                  INTEGER PRIMARY KEY,
    name                TEXT    NOT NULL DEFAULT '',
    controller_type     TEXT    NOT NULL CHECK (controller_type IN ('POWER_FACTOR', 'VOLT_VAR')),
    supported_by        TEXT    NOT NULL
        CHECK (supported_by IN ('battery-only','solar-only','battery-and-solar')),
    -- POWER_FACTOR subtype:
    power_factor        REAL    NULL CHECK (power_factor >= -1 AND power_factor <= 1),
    -- VOLT_VAR subtype:
    volt_var_curve_id   INTEGER NULL REFERENCES curves (id) ON DELETE SET NULL,
    var_follow          INTEGER NULL CHECK (var_follow IN (0, 1))
);

-- Active power control setting for an inverter.
-- Subtypes: VOLT_WATT, PEAK_SHAVING, CAPACITY_FIRMING, TIME_BASED,
--           SELF_CONSUMPTION, TIME_OF_USE, DEMAND_CHARGE.
CREATE TABLE inverter_active_power_controls (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL DEFAULT '',
    controller_type             TEXT    NOT NULL CHECK (controller_type IN (
                                    'VOLT_WATT','PEAK_SHAVING','CAPACITY_FIRMING',
                                    'TIME_BASED','SELF_CONSUMPTION',
                                    'TIME_OF_USE','DEMAND_CHARGE')),
    supported_by                TEXT    NOT NULL
        CHECK (supported_by IN ('battery-only','solar-only','battery-and-solar')),
    -- VOLT_WATT subtype:
    volt_watt_curve_id          INTEGER NULL REFERENCES curves (id) ON DELETE SET NULL,
    -- PEAK_SHAVING subtype:
    peak_shaving_target         REAL    NULL CHECK (peak_shaving_target >= 0),
    peak_shaving_target_unit    TEXT    NULL DEFAULT 'watt',
    base_loading_target         REAL    NULL CHECK (base_loading_target >= 0),
    base_loading_target_unit    TEXT    NULL DEFAULT 'watt',
    -- CAPACITY_FIRMING subtype:
    max_active_power_roc        REAL    NULL,
    max_active_power_roc_unit   TEXT    NULL DEFAULT 'watt/second',
    min_active_power_roc        REAL    NULL,
    min_active_power_roc_unit   TEXT    NULL DEFAULT 'watt/second',
    -- TIME_BASED subtype (times stored as 'HH:MM:SS'):
    charging_start_time         TEXT    NULL,
    charging_end_time           TEXT    NULL,
    discharging_start_time      TEXT    NULL,
    discharging_end_time        TEXT    NULL,
    charging_power              REAL    NULL CHECK (charging_power >= 0),
    charging_power_unit         TEXT    NULL DEFAULT 'watt',
    discharging_power           REAL    NULL CHECK (discharging_power >= 0),
    discharging_power_unit      TEXT    NULL DEFAULT 'watt',
    -- TIME_OF_USE / DEMAND_CHARGE subtype:
    tariff_id                   INTEGER NULL,
    CONSTRAINT check_volt_watt  CHECK (controller_type != 'VOLT_WATT'    OR volt_watt_curve_id IS NOT NULL),
    CONSTRAINT check_peak_shave CHECK (controller_type != 'PEAK_SHAVING' OR
        (peak_shaving_target IS NOT NULL AND base_loading_target IS NOT NULL)),
    CONSTRAINT check_cap_firm   CHECK (controller_type != 'CAPACITY_FIRMING' OR
        (max_active_power_roc IS NOT NULL AND min_active_power_roc IS NOT NULL)),
    CONSTRAINT check_time       CHECK (controller_type != 'TIME_BASED' OR
        (charging_start_time IS NOT NULL AND discharging_start_time IS NOT NULL))
);

-- Top-level inverter controller (used by DistributionSolar and DistributionBattery).
CREATE TABLE inverter_controllers (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL DEFAULT '',
    prioritize_active_power     INTEGER NOT NULL CHECK (prioritize_active_power IN (0, 1)),
    night_mode                  INTEGER NOT NULL CHECK (night_mode IN (0, 1)),
    active_power_control_id     INTEGER NULL
        REFERENCES inverter_active_power_controls  (id) ON DELETE SET NULL,
    reactive_power_control_id   INTEGER NULL
        REFERENCES inverter_reactive_power_controls (id) ON DELETE SET NULL
);

-- ============================================================
-- DISTRIBUTION COMPONENTS
-- ============================================================

-- DistributionLoad: ZIP load attached to a bus.
CREATE TABLE distribution_loads (
    id                  INTEGER PRIMARY KEY,
    name                TEXT    NOT NULL UNIQUE,
    bus_id              INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id       INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id           INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    load_equipment_id   INTEGER NOT NULL REFERENCES load_equipment           (id),
    in_service          INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);

-- Ordered phase list for a DistributionLoad (replaces phases JSON array).
CREATE TABLE distribution_load_phases (
    id              INTEGER PRIMARY KEY,
    load_id         INTEGER NOT NULL REFERENCES distribution_loads (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (load_id, position_index),
    UNIQUE (load_id, phase)
);

-- DistributionSolar: PV system attached to a bus.
-- inverter_controller_id replaces the former controller JSON column.
CREATE TABLE distribution_solar (
    id                      INTEGER PRIMARY KEY,
    name                    TEXT    NOT NULL UNIQUE,
    bus_id                  INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id           INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id               INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    irradiance              REAL    NOT NULL CHECK (irradiance >= 0),
    irradiance_unit         TEXT    NOT NULL DEFAULT 'watt/meter^2',
    active_power            REAL    NOT NULL CHECK (active_power >= 0),
    active_power_unit       TEXT    NOT NULL DEFAULT 'watt',
    reactive_power          REAL    NOT NULL,
    reactive_power_unit     TEXT    NOT NULL DEFAULT 'watt',
    solar_equipment_id      INTEGER NOT NULL REFERENCES solar_equipment    (id),
    inverter_equipment_id   INTEGER NOT NULL REFERENCES inverter_equipment  (id),
    inverter_controller_id  INTEGER NULL
        REFERENCES inverter_controllers (id) ON DELETE SET NULL,
    in_service              INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);

-- Ordered phase list for a DistributionSolar (replaces phases JSON array).
CREATE TABLE distribution_solar_phases (
    id              INTEGER PRIMARY KEY,
    solar_id        INTEGER NOT NULL REFERENCES distribution_solar (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (solar_id, position_index),
    UNIQUE (solar_id, phase)
);

-- DistributionBattery: battery energy storage attached to a bus.
-- inverter_controller_id replaces the former controller JSON column.
CREATE TABLE distribution_batteries (
    id                      INTEGER PRIMARY KEY,
    name                    TEXT    NOT NULL UNIQUE,
    bus_id                  INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id           INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id               INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    active_power            REAL    NOT NULL,
    active_power_unit       TEXT    NOT NULL DEFAULT 'watt',
    reactive_power          REAL    NOT NULL,
    reactive_power_unit     TEXT    NOT NULL DEFAULT 'watt',
    battery_equipment_id    INTEGER NOT NULL REFERENCES battery_equipment   (id),
    inverter_equipment_id   INTEGER NOT NULL REFERENCES inverter_equipment   (id),
    inverter_controller_id  INTEGER NULL
        REFERENCES inverter_controllers (id) ON DELETE SET NULL,
    in_service              INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);

-- Ordered phase list for a DistributionBattery (replaces phases JSON array).
CREATE TABLE distribution_battery_phases (
    id              INTEGER PRIMARY KEY,
    battery_id      INTEGER NOT NULL REFERENCES distribution_batteries (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (battery_id, position_index),
    UNIQUE (battery_id, phase)
);

-- DistributionCapacitor: shunt capacitor bank attached to a bus.
CREATE TABLE distribution_capacitors (
    id                      INTEGER PRIMARY KEY,
    name                    TEXT    NOT NULL UNIQUE,
    bus_id                  INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id           INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id               INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    capacitor_equipment_id  INTEGER NOT NULL REFERENCES capacitor_equipment      (id),
    in_service              INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);

-- Per-phase controller for a DistributionCapacitor (replaces controllers JSON array).
-- controller_type discriminates the five CapacitorControllerBase subtypes.
CREATE TABLE capacitor_controllers (
    id                      INTEGER PRIMARY KEY,
    capacitor_id            INTEGER NOT NULL
        REFERENCES distribution_capacitors (id) ON DELETE CASCADE,
    position_index          INTEGER NOT NULL CHECK (position_index >= 0),
    name                    TEXT    NOT NULL DEFAULT '',
    controller_type         TEXT    NOT NULL CHECK (controller_type IN (
                                'VOLTAGE','ACTIVE_POWER','REACTIVE_POWER','CURRENT','DAILY_TIMED')),
    -- CapacitorControllerBase shared fields:
    delay_on                REAL    NULL CHECK (delay_on  >= 0),
    delay_on_unit           TEXT    NULL DEFAULT 'second',
    delay_off               REAL    NULL CHECK (delay_off >= 0),
    delay_off_unit          TEXT    NULL DEFAULT 'second',
    dead_time               REAL    NULL CHECK (dead_time >= 0),
    dead_time_unit          TEXT    NULL DEFAULT 'second',
    -- VOLTAGE subtype (VoltageCapacitorController):
    on_voltage              REAL    NULL CHECK (on_voltage  > 0),
    on_voltage_unit         TEXT    NULL DEFAULT 'volt',
    off_voltage             REAL    NULL CHECK (off_voltage > 0),
    off_voltage_unit        TEXT    NULL DEFAULT 'volt',
    pt_ratio                REAL    NULL CHECK (pt_ratio >= 0),
    -- ACTIVE_POWER subtype (ActivePowerCapacitorController):
    on_active_power         REAL    NULL CHECK (on_active_power  >= 0),
    on_active_power_unit    TEXT    NULL DEFAULT 'watt',
    off_active_power        REAL    NULL CHECK (off_active_power >  0),
    off_active_power_unit   TEXT    NULL DEFAULT 'watt',
    -- REACTIVE_POWER subtype (ReactivePowerCapacitorController):
    on_reactive_power       REAL    NULL CHECK (on_reactive_power  > 0),
    on_reactive_power_unit  TEXT    NULL DEFAULT 'var',
    off_reactive_power      REAL    NULL CHECK (off_reactive_power > 0),
    off_reactive_power_unit TEXT    NULL DEFAULT 'var',
    -- CURRENT subtype (CurrentCapacitorController):
    on_current              REAL    NULL CHECK (on_current  > 0),
    on_current_unit         TEXT    NULL DEFAULT 'ampere',
    off_current             REAL    NULL CHECK (off_current >= 0),
    off_current_unit        TEXT    NULL DEFAULT 'ampere',
    ct_ratio                REAL    NULL CHECK (ct_ratio >= 0),
    -- DAILY_TIMED subtype (DailyTimedCapacitorController) -- stored as 'HH:MM:SS':
    on_time                 TEXT    NULL,
    off_time                TEXT    NULL,
    UNIQUE (capacitor_id, position_index)
);

-- Ordered phase list for a DistributionCapacitor (replaces phases JSON array).
CREATE TABLE distribution_capacitor_phases (
    id              INTEGER PRIMARY KEY,
    capacitor_id    INTEGER NOT NULL REFERENCES distribution_capacitors (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (capacitor_id, position_index),
    UNIQUE (capacitor_id, phase)
);

-- DistributionVoltageSource: Thevenin equivalent voltage source at a bus.
CREATE TABLE distribution_voltage_sources (
    id                              INTEGER PRIMARY KEY,
    name                            TEXT    NOT NULL UNIQUE,
    bus_id                          INTEGER NOT NULL
        REFERENCES distribution_buses           (id) ON DELETE CASCADE,
    substation_id                   INTEGER NOT NULL
        REFERENCES distribution_substations     (id) ON DELETE CASCADE,
    feeder_id                       INTEGER NOT NULL
        REFERENCES distribution_feeders         (id) ON DELETE CASCADE,
    voltage_source_equipment_id     INTEGER NOT NULL
        REFERENCES voltage_source_equipment     (id),
    in_service                      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);

-- Ordered phase list for a DistributionVoltageSource (replaces phases JSON array).
CREATE TABLE distribution_voltage_source_phases (
    id              INTEGER PRIMARY KEY,
    vsource_id      INTEGER NOT NULL REFERENCES distribution_voltage_sources (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (vsource_id, position_index),
    UNIQUE (vsource_id, phase)
);

-- ============================================================
-- BRANCH COMPONENTS -- Lines
-- ============================================================
-- from_bus_id / to_bus_id are the explicit FK columns; no buses JSON needed.

-- MatrixImpedanceBranch: full matrix line model.
CREATE TABLE matrix_impedance_branches (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    from_bus_id     INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    to_bus_id       INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id   INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    length          REAL    NOT NULL CHECK (length > 0),
    length_unit     TEXT    NOT NULL DEFAULT 'meter',
    equipment_id    INTEGER NOT NULL REFERENCES matrix_impedance_branch_equipment (id),
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
-- Ordered phase list for a MatrixImpedanceBranch (replaces phases JSON array).
CREATE TABLE matrix_impedance_branch_phases (
    id              INTEGER PRIMARY KEY,
    branch_id       INTEGER NOT NULL REFERENCES matrix_impedance_branches (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (branch_id, position_index),
    UNIQUE (branch_id, phase)
);
-- Thermal limits junction (replaces thermal_limit_ids JSON array).
CREATE TABLE matrix_impedance_branch_thermal_limits (
    branch_id            INTEGER NOT NULL
        REFERENCES matrix_impedance_branches (id) ON DELETE CASCADE,
    thermal_limit_set_id INTEGER NOT NULL
        REFERENCES thermal_limit_sets        (id) ON DELETE CASCADE,
    PRIMARY KEY (branch_id, thermal_limit_set_id)
);

-- SequenceImpedanceBranch: positive/zero sequence line model.
CREATE TABLE sequence_impedance_branches (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    from_bus_id     INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    to_bus_id       INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id   INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    length          REAL    NOT NULL CHECK (length > 0),
    length_unit     TEXT    NOT NULL DEFAULT 'meter',
    equipment_id    INTEGER NOT NULL REFERENCES sequence_impedance_branch_equipment (id),
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
CREATE TABLE sequence_impedance_branch_phases (
    id              INTEGER PRIMARY KEY,
    branch_id       INTEGER NOT NULL REFERENCES sequence_impedance_branches (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (branch_id, position_index),
    UNIQUE (branch_id, phase)
);
CREATE TABLE sequence_impedance_branch_thermal_limits (
    branch_id            INTEGER NOT NULL
        REFERENCES sequence_impedance_branches (id) ON DELETE CASCADE,
    thermal_limit_set_id INTEGER NOT NULL
        REFERENCES thermal_limit_sets          (id) ON DELETE CASCADE,
    PRIMARY KEY (branch_id, thermal_limit_set_id)
);

-- GeometryBranch: impedance computed from conductor geometry.
CREATE TABLE geometry_branches (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    from_bus_id     INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    to_bus_id       INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id   INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    length          REAL    NOT NULL CHECK (length > 0),
    length_unit     TEXT    NOT NULL DEFAULT 'meter',
    equipment_id    INTEGER NOT NULL REFERENCES geometry_branch_equipment (id),
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
CREATE TABLE geometry_branch_phases (
    id              INTEGER PRIMARY KEY,
    branch_id       INTEGER NOT NULL REFERENCES geometry_branches (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (branch_id, position_index),
    UNIQUE (branch_id, phase)
);
CREATE TABLE geometry_branch_thermal_limits (
    branch_id            INTEGER NOT NULL REFERENCES geometry_branches  (id) ON DELETE CASCADE,
    thermal_limit_set_id INTEGER NOT NULL REFERENCES thermal_limit_sets (id) ON DELETE CASCADE,
    PRIMARY KEY (branch_id, thermal_limit_set_id)
);

-- ============================================================
-- BRANCH COMPONENTS -- Protective / Switching Devices
-- ============================================================

-- MatrixImpedanceFuse.
CREATE TABLE matrix_impedance_fuses (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    from_bus_id     INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    to_bus_id       INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id   INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    length          REAL    NOT NULL CHECK (length > 0),
    length_unit     TEXT    NOT NULL DEFAULT 'meter',
    equipment_id    INTEGER NOT NULL REFERENCES matrix_impedance_fuse_equipment (id),
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
-- Ordered phase list for a fuse (replaces phases JSON array).
CREATE TABLE matrix_impedance_fuse_phases (
    id              INTEGER PRIMARY KEY,
    fuse_id         INTEGER NOT NULL REFERENCES matrix_impedance_fuses (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (fuse_id, position_index),
    UNIQUE (fuse_id, phase)
);
-- Per-phase closed/open state for a fuse (replaces is_closed JSON array).
CREATE TABLE fuse_phase_states (
    id              INTEGER PRIMARY KEY,
    fuse_id         INTEGER NOT NULL REFERENCES matrix_impedance_fuses (id) ON DELETE CASCADE,
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    phase           TEXT    NOT NULL REFERENCES phases (name),
    is_closed       INTEGER NOT NULL CHECK (is_closed IN (0, 1)),
    UNIQUE (fuse_id, position_index)
);

-- Recloser controller tables.
-- ground_delayed/fast, phase_delayed/fast reference time_current_curves.
CREATE TABLE recloser_controllers (
    id                          INTEGER PRIMARY KEY,
    name                        TEXT    NOT NULL DEFAULT '',
    delay                       REAL    NOT NULL CHECK (delay >= 0),
    delay_unit                  TEXT    NOT NULL DEFAULT 'second',
    ground_delayed_curve_id     INTEGER NOT NULL
        REFERENCES time_current_curves (id) ON DELETE RESTRICT,
    ground_fast_curve_id        INTEGER NOT NULL
        REFERENCES time_current_curves (id) ON DELETE RESTRICT,
    phase_delayed_curve_id      INTEGER NOT NULL
        REFERENCES time_current_curves (id) ON DELETE RESTRICT,
    phase_fast_curve_id         INTEGER NOT NULL
        REFERENCES time_current_curves (id) ON DELETE RESTRICT,
    num_fast_ops                INTEGER NOT NULL CHECK (num_fast_ops >= 0),
    num_shots                   INTEGER NOT NULL CHECK (num_shots >= 1),
    reset_time                  REAL    NOT NULL CHECK (reset_time >= 0),
    reset_time_unit             TEXT    NOT NULL DEFAULT 'second',
    equipment_id                INTEGER NOT NULL
        REFERENCES recloser_controller_equipment (id) ON DELETE RESTRICT
);
-- Reclose intervals ordered array (replaces reclose_intervals Time[] array).
CREATE TABLE recloser_reclose_intervals (
    id                      INTEGER PRIMARY KEY,
    recloser_controller_id  INTEGER NOT NULL
        REFERENCES recloser_controllers (id) ON DELETE CASCADE,
    position_index          INTEGER NOT NULL CHECK (position_index >= 0),
    interval_value          REAL    NOT NULL CHECK (interval_value >= 0),
    interval_unit           TEXT    NOT NULL DEFAULT 'second',
    UNIQUE (recloser_controller_id, position_index)
);

-- MatrixImpedanceRecloser.
-- controller_id replaces the former controller JSON column.
CREATE TABLE matrix_impedance_reclosers (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    from_bus_id     INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    to_bus_id       INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id   INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    length          REAL    NOT NULL CHECK (length > 0),
    length_unit     TEXT    NOT NULL DEFAULT 'meter',
    equipment_id    INTEGER NOT NULL REFERENCES matrix_impedance_recloser_equipment (id),
    controller_id   INTEGER NOT NULL REFERENCES recloser_controllers     (id) ON DELETE RESTRICT,
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
-- Ordered phase list for a recloser (replaces phases JSON array).
CREATE TABLE matrix_impedance_recloser_phases (
    id              INTEGER PRIMARY KEY,
    recloser_id     INTEGER NOT NULL REFERENCES matrix_impedance_reclosers (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (recloser_id, position_index),
    UNIQUE (recloser_id, phase)
);
-- Per-phase closed/open state for a recloser (replaces is_closed JSON array).
CREATE TABLE recloser_phase_states (
    id              INTEGER PRIMARY KEY,
    recloser_id     INTEGER NOT NULL REFERENCES matrix_impedance_reclosers (id) ON DELETE CASCADE,
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    phase           TEXT    NOT NULL REFERENCES phases (name),
    is_closed       INTEGER NOT NULL CHECK (is_closed IN (0, 1)),
    UNIQUE (recloser_id, position_index)
);

-- MatrixImpedanceSwitch.
CREATE TABLE matrix_impedance_switches (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    from_bus_id     INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    to_bus_id       INTEGER NOT NULL REFERENCES distribution_buses       (id) ON DELETE CASCADE,
    substation_id   INTEGER NOT NULL REFERENCES distribution_substations (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL REFERENCES distribution_feeders     (id) ON DELETE CASCADE,
    length          REAL    NOT NULL CHECK (length > 0),
    length_unit     TEXT    NOT NULL DEFAULT 'meter',
    equipment_id    INTEGER NOT NULL REFERENCES matrix_impedance_switch_equipment (id),
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
-- Ordered phase list for a switch (replaces phases JSON array).
CREATE TABLE matrix_impedance_switch_phases (
    id              INTEGER PRIMARY KEY,
    switch_id       INTEGER NOT NULL REFERENCES matrix_impedance_switches (id) ON DELETE CASCADE,
    phase           TEXT    NOT NULL REFERENCES phases (name),
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    UNIQUE (switch_id, position_index),
    UNIQUE (switch_id, phase)
);
-- Per-phase closed/open state for a switch (replaces is_closed JSON array).
CREATE TABLE switch_phase_states (
    id              INTEGER PRIMARY KEY,
    switch_id       INTEGER NOT NULL REFERENCES matrix_impedance_switches (id) ON DELETE CASCADE,
    position_index  INTEGER NOT NULL CHECK (position_index >= 0),
    phase           TEXT    NOT NULL REFERENCES phases (name),
    is_closed       INTEGER NOT NULL CHECK (is_closed IN (0, 1)),
    UNIQUE (switch_id, position_index)
);

-- ============================================================
-- TRANSFORMER / REGULATOR COMPONENTS
-- ============================================================

-- DistributionTransformer.
-- bus_ids JSON replaced by transformer_winding_buses.
-- winding_phases JSON replaced by transformer_winding_phases.
CREATE TABLE distribution_transformers (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    substation_id   INTEGER NOT NULL
        REFERENCES distribution_substations          (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL
        REFERENCES distribution_feeders               (id) ON DELETE CASCADE,
    equipment_id    INTEGER NOT NULL
        REFERENCES distribution_transformer_equipment (id),
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
-- Ordered winding-to-bus mapping (replaces bus_ids JSON array).
CREATE TABLE transformer_winding_buses (
    id              INTEGER PRIMARY KEY,
    transformer_id  INTEGER NOT NULL REFERENCES distribution_transformers (id) ON DELETE CASCADE,
    winding_index   INTEGER NOT NULL CHECK (winding_index >= 0),
    bus_id          INTEGER NOT NULL REFERENCES distribution_buses        (id) ON DELETE CASCADE,
    UNIQUE (transformer_id, winding_index)
);
-- Ordered per-phase list for each winding (replaces winding_phases JSON array of arrays).
CREATE TABLE transformer_winding_phases (
    id              INTEGER PRIMARY KEY,
    transformer_id  INTEGER NOT NULL REFERENCES distribution_transformers (id) ON DELETE CASCADE,
    winding_index   INTEGER NOT NULL CHECK (winding_index >= 0),
    phase           TEXT    NOT NULL REFERENCES phases (name),
    phase_index     INTEGER NOT NULL CHECK (phase_index >= 0),
    UNIQUE (transformer_id, winding_index, phase_index),
    UNIQUE (transformer_id, winding_index, phase)
);

-- DistributionRegulator.
-- bus_ids JSON replaced by regulator_winding_buses.
-- winding_phases JSON replaced by regulator_winding_phases.
-- controllers JSON replaced by regulator_controllers.
CREATE TABLE distribution_regulators (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    substation_id   INTEGER NOT NULL
        REFERENCES distribution_substations          (id) ON DELETE CASCADE,
    feeder_id       INTEGER NOT NULL
        REFERENCES distribution_feeders               (id) ON DELETE CASCADE,
    equipment_id    INTEGER NOT NULL
        REFERENCES distribution_transformer_equipment (id),
    in_service      INTEGER NOT NULL DEFAULT 1 CHECK (in_service IN (0, 1))
);
-- Ordered winding-to-bus mapping for a regulator.
CREATE TABLE regulator_winding_buses (
    id              INTEGER PRIMARY KEY,
    regulator_id    INTEGER NOT NULL REFERENCES distribution_regulators (id) ON DELETE CASCADE,
    winding_index   INTEGER NOT NULL CHECK (winding_index >= 0),
    bus_id          INTEGER NOT NULL REFERENCES distribution_buses      (id) ON DELETE CASCADE,
    UNIQUE (regulator_id, winding_index)
);
-- Ordered per-phase list for each winding of a regulator.
CREATE TABLE regulator_winding_phases (
    id              INTEGER PRIMARY KEY,
    regulator_id    INTEGER NOT NULL REFERENCES distribution_regulators (id) ON DELETE CASCADE,
    winding_index   INTEGER NOT NULL CHECK (winding_index >= 0),
    phase           TEXT    NOT NULL REFERENCES phases (name),
    phase_index     INTEGER NOT NULL CHECK (phase_index >= 0),
    UNIQUE (regulator_id, winding_index, phase_index),
    UNIQUE (regulator_id, winding_index, phase)
);
-- Per-phase regulator controller (replaces controllers JSON array).
-- controlled_bus_id and controlled_phase replace the embedded DistributionBus object.
CREATE TABLE regulator_controllers (
    id                  INTEGER PRIMARY KEY,
    regulator_id        INTEGER NOT NULL REFERENCES distribution_regulators (id) ON DELETE CASCADE,
    position_index      INTEGER NOT NULL CHECK (position_index >= 0),
    name                TEXT    NOT NULL DEFAULT '',
    delay               REAL    NULL CHECK (delay >= 0),
    delay_unit          TEXT    NULL DEFAULT 'second',
    v_setpoint          REAL    NOT NULL CHECK (v_setpoint > 0),
    v_setpoint_unit     TEXT    NOT NULL DEFAULT 'volt',
    min_v_limit         REAL    NOT NULL CHECK (min_v_limit > 0),
    min_v_limit_unit    TEXT    NOT NULL DEFAULT 'volt',
    max_v_limit         REAL    NOT NULL CHECK (max_v_limit > 0),
    max_v_limit_unit    TEXT    NOT NULL DEFAULT 'volt',
    pt_ratio            REAL    NOT NULL CHECK (pt_ratio >= 0),
    use_ldc             INTEGER NOT NULL CHECK (use_ldc IN (0, 1)),
    is_reversible       INTEGER NOT NULL CHECK (is_reversible IN (0, 1)),
    ldc_R               REAL    NULL CHECK (ldc_R >= 0),
    ldc_R_unit          TEXT    NULL DEFAULT 'volt',
    ldc_X               REAL    NULL CHECK (ldc_X >= 0),
    ldc_X_unit          TEXT    NULL DEFAULT 'volt',
    ct_primary          REAL    NULL CHECK (ct_primary >= 0),
    ct_primary_unit     TEXT    NULL DEFAULT 'ampere',
    max_step            INTEGER NOT NULL CHECK (max_step >= 0),
    bandwidth           REAL    NOT NULL CHECK (bandwidth >= 0),
    bandwidth_unit      TEXT    NOT NULL DEFAULT 'volt',
    controlled_bus_id   INTEGER NOT NULL REFERENCES distribution_buses (id) ON DELETE RESTRICT,
    controlled_phase    TEXT    NOT NULL REFERENCES phases (name),
    UNIQUE (regulator_id, position_index)
);

-- ============================================================
-- TIME SERIES ASSOCIATIONS
-- ============================================================
CREATE TABLE time_series_associations (
    id                          INTEGER PRIMARY KEY,
    time_series_uuid            TEXT    NOT NULL,
    time_series_type            TEXT    NOT NULL,
    initial_timestamp           TEXT    NOT NULL,
    resolution                  TEXT    NOT NULL,
    horizon                     TEXT    NULL,
    "interval"                  TEXT    NULL,
    window_count                INTEGER NULL,
    length                      INTEGER NULL,
    name                        TEXT    NOT NULL,
    owner_id                    INTEGER NOT NULL,
    owner_type                  TEXT    NOT NULL,
    owner_category              TEXT    NOT NULL,
    features                    TEXT    NOT NULL,
    scaling_factor_multiplier   TEXT    NULL,
    metadata_uuid               TEXT    NOT NULL,
    units                       TEXT    NULL
);

CREATE UNIQUE INDEX dist_ts_by_owner_name_res_feat
    ON time_series_associations (owner_id, time_series_type, name, resolution, features);

CREATE INDEX dist_ts_by_uuid
    ON time_series_associations (time_series_uuid);
