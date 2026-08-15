from core import DnsDeliverabilityInspector, DnsInspectionResult
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/tools", tags=["Tools"])
_dns_inspector = DnsDeliverabilityInspector()


@router.get("/dns-check", response_model=None)
async def check_domain_dns_deliverability(
    domain: str = Query(..., description="Domain name or sender email (e.g. acme.com)"),
) -> DnsInspectionResult:
    """Analyze domain SPF, DMARC, and MX records to calculate Deliverability Readiness Score."""
    if not domain or len(domain.strip()) < 3:
        raise HTTPException(status_code=400, detail="Invalid domain parameter")

    result = await _dns_inspector.inspect(domain)
    return result
