import structlog

from src.config import settings

log = structlog.get_logger()


async def send_escalation_notification(
    audit_id: str,
    total_order_value: float,
    risk_score: float,
    reason: str | None = None,
) -> bool:
    if not settings.slack_webhook_url:
        log.info("slack_notification_skipped", reason="no webhook configured")
        return False

    payload = {
        "text": (
            f":warning: *Inventory Replenishment — Manager Approval Required*\n"
            f"• Audit: `{audit_id}`\n"
            f"• Total Order Value: `${total_order_value:,.2f}`\n"
            f"• Risk Score: {risk_score:.2f}\n"
            f"• Reason: {reason or 'Exceeds threshold'}"
        ),
    }

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(settings.slack_webhook_url, json=payload)
            resp.raise_for_status()
        log.info("slack_notification_sent", audit_id=audit_id)
        return True
    except Exception as e:
        log.error("slack_notification_failed", audit_id=audit_id, error=str(e))
        return False
