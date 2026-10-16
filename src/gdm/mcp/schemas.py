"""Pydantic schemas for MCP tool inputs and outputs."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    """Types of validation errors."""

    PHASE_MISMATCH = "phase_mismatch"
    MATRIX_DIMENSION = "matrix_dimension"
    ARRAY_LENGTH = "array_length"
    MISSING_REFERENCE = "missing_reference"
    INVALID_VALUE = "invalid_value"
    PYDANTIC_VALIDATION = "pydantic_validation"
    OTHER = "other"


class ValidationIssue(BaseModel):
    """A single validation issue in a component."""

    component_id: int
    component_type: str
    component_name: str
    field_path: str
    error_type: ErrorType
    message: str
    current_value: Optional[Any] = None
    expected_value: Optional[Any] = None


class ValidationReport(BaseModel):
    """Complete validation report for a system."""

    system_name: str
    total_components: int
    valid_components: int
    invalid_components: int
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if system is valid."""
        return len(self.issues) == 0


class FixStrategy(str, Enum):
    """Fix strategies for validation errors."""

    ALIGN_PHASES = "align_phases"
    RESIZE_MATRIX = "resize_matrix"
    ADJUST_ARRAY_LENGTH = "adjust_array_length"
    REMOVE_INVALID = "remove_invalid"
    SET_DEFAULT = "set_default"


class ConfidenceLevel(str, Enum):
    """Confidence level for fix suggestions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FixSuggestion(BaseModel):
    """A suggested fix for a validation issue."""

    issue: ValidationIssue
    strategy: FixStrategy
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceLevel
    risk_level: str = "low"  # low, medium, high


class ChangeLogEntry(BaseModel):
    """A single change made during fix application."""

    component_id: int
    component_type: str
    component_name: str
    field_path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    fix_strategy: FixStrategy
    timestamp: str


class FixResult(BaseModel):
    """Result of applying fixes to a system."""

    success: bool
    fixes_applied: int
    fixes_failed: int
    change_log: list[ChangeLogEntry] = Field(default_factory=list)
    remaining_issues: list[ValidationIssue] = Field(default_factory=list)
    error_message: Optional[str] = None


class ComponentSummary(BaseModel):
    """Summary of components by type."""

    component_type: str
    count: int
    with_timeseries: int = 0


class SubstationSummary(BaseModel):
    """Summary of components in a substation."""

    name: str
    feeder_count: int
    component_count: int
    bus_count: int


class FeederSummary(BaseModel):
    """Summary of components in a feeder."""

    name: str
    substation: Optional[str] = None
    component_count: int
    bus_count: int


class SystemSummary(BaseModel):
    """Complete system summary."""

    name: str
    total_components: int
    components_by_type: list[ComponentSummary] = Field(default_factory=list)
    substations: list[SubstationSummary] = Field(default_factory=list)
    feeders: list[FeederSummary] = Field(default_factory=list)
    has_timeseries: bool
    timeseries_count: int = 0


class TopologyMetrics(BaseModel):
    """Network topology metrics."""

    node_count: int
    edge_count: int
    has_source: bool
    source_bus_name: Optional[str] = None
    cycle_count: int
    island_count: int
    is_radial: bool
    max_degree: int


class MergeConflict(BaseModel):
    """A conflict detected during merge."""

    conflict_type: str  # "name", "incompatible_settings"
    component_type: Optional[str] = None
    identifier: str
    system_indices: list[int]  # Which input systems have this conflict
    details: str


class MergeReport(BaseModel):
    """Report from merging systems."""

    success: bool
    output_system_name: str
    input_system_count: int
    total_components_merged: int
    components_by_type: dict[str, int] = Field(default_factory=dict)
    timeseries_transferred: int = 0
    conflicts: list[MergeConflict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class SplitReport(BaseModel):
    """Report from splitting a system."""

    success: bool
    input_system_name: str
    output_count: int
    split_by: str  # "substation" or "feeder"
    subsystems: dict[str, int] = Field(default_factory=dict)  # name -> component count
    unassigned_components: int = 0
    timeseries_preserved: bool = True
    warnings: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class ComponentFilter(BaseModel):
    """Filters for querying components."""

    component_types: Optional[list[str]] = None
    substation: Optional[str] = None
    feeder: Optional[str] = None
    phases: Optional[list[str]] = None
    in_service: Optional[bool] = None
    has_timeseries: Optional[bool] = None


class ComponentInfo(BaseModel):
    """Basic information about a component."""

    component_id: int
    component_type: str
    name: str
    substation: Optional[str] = None
    feeder: Optional[str] = None
    phases: Optional[list[str]] = None
    in_service: Optional[bool] = None


class TimeSeriesInfo(BaseModel):
    """Information about time series data."""

    component_id: int
    component_name: str
    component_type: str
    timeseries_type: str
    variable_name: str
    length: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


# Documentation/Knowledge schemas
class DocumentationSearchResult(BaseModel):
    """A search result from documentation."""

    title: str
    file_path: str
    content: str
    relevance_score: float = 0.0


class APIReferenceResult(BaseModel):
    """API reference information for a component or class."""

    component_name: str
    description: str
    fields: list[dict[str, Any]] = Field(default_factory=list)
    methods: list[dict[str, str]] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class CodeExample(BaseModel):
    """A code example from documentation."""

    title: str
    code: str
    description: str
    file_path: str


class ComponentInfoBasic(BaseModel):
    """Basic information about an available component type."""

    name: str
    description: str
    category: str
