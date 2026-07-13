class InventoryAgentError(Exception):
    """Base exception for the inventory replenishment agent."""


class IngestionError(InventoryAgentError):
    """Raised when document ingestion fails."""


class ConfigError(InventoryAgentError):
    """Raised on invalid configuration."""


class SupplierNotFoundError(InventoryAgentError):
    """Raised when no suitable supplier is found."""


class EscalationError(InventoryAgentError):
    """Raised when human escalation fails."""


class InsufficientStockError(InventoryAgentError):
    """Raised when stock cannot be replenished through normal channels."""
