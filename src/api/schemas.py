from datetime import datetime

from pydantic import BaseModel


class AuditTriggerRequest(BaseModel):
    skus: list[str] | None = None
    force_approval: bool = False


class StockLevel(BaseModel):
    sku: str
    current_stock: int
    reorder_point: float
    shortfall: int


class DemandForecast(BaseModel):
    sku: str
    predicted_daily_demand: float
    lead_time_days: int
    confidence: float


class SupplierProposal(BaseModel):
    supplier_name: str
    sku: str
    quantity: int
    unit_price: float
    total_cost: float
    lead_time_days: int
    score: float


class OrderProposal(BaseModel):
    supplier_name: str
    sku: str
    quantity: int
    total_cost: float
    lead_time_days: int


class EscalationInfo(BaseModel):
    requires_approval: bool
    total_order_value: float
    risk_score: float
    reason: str | None = None


class AuditResult(BaseModel):
    audit_id: str
    triggered_at: datetime
    status: str
    stock_levels: list[StockLevel] = []
    deficits: list[str] = []
    order_proposals: list[OrderProposal] = []
    escalation: EscalationInfo | None = None
    approved: bool | None = None
    final_message: str | None = None


class ApprovalRequest(BaseModel):
    audit_id: str
    approved: bool


class HealthResponse(BaseModel):
    status: str = "ok"


class VersionResponse(BaseModel):
    version: str = "0.1.0"
    name: str = "inventory-replenishment-agent"
