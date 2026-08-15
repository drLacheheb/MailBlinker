import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List


@dataclass
class DmarcRecordEntry:
    source_ip: str
    count: int
    disposition: str  # "none", "quarantine", "reject"
    dkim_result: str  # "pass", "fail"
    spf_result: str  # "pass", "fail"
    header_from: str


@dataclass
class DmarcReportSummary:
    org_name: str
    report_id: str
    domain: str
    total_messages: int
    passed_count: int
    failed_count: int
    records: List[DmarcRecordEntry] = field(default_factory=list)


def parse_dmarc_rua_xml(xml_content: str) -> DmarcReportSummary:
    """Parse RFC 7489 DMARC XML Aggregate Feedback Report (rua)."""
    root = ET.fromstring(xml_content)

    org_name = root.findtext(".//report_metadata/org_name", default="Unknown Org")
    report_id = root.findtext(".//report_metadata/report_id", default="unknown")
    domain = root.findtext(".//policy_published/domain", default="")

    records: List[DmarcRecordEntry] = []
    total_messages = 0
    passed_count = 0
    failed_count = 0

    for rec in root.findall(".//record"):
        row = rec.find("row")
        source_ip = row.findtext("source_ip", default="0.0.0.0") if row is not None else "0.0.0.0"
        count_str = row.findtext("count", default="1") if row is not None else "1"
        try:
            count = int(count_str)
        except ValueError:
            count = 1

        policy_eval = row.find("policy_evaluated") if row is not None else None
        disp = (
            policy_eval.findtext("disposition", default="none")
            if policy_eval is not None
            else "none"
        )
        dkim_res = (
            policy_eval.findtext("dkim", default="fail") if policy_eval is not None else "fail"
        )
        spf_res = policy_eval.findtext("spf", default="fail") if policy_eval is not None else "fail"

        identifiers = rec.find("identifiers")
        header_from = (
            identifiers.findtext("header_from", default="") if identifiers is not None else ""
        )

        is_pass = dkim_res == "pass" or spf_res == "pass"
        total_messages += count
        if is_pass:
            passed_count += count
        else:
            failed_count += count

        records.append(
            DmarcRecordEntry(
                source_ip=source_ip,
                count=count,
                disposition=disp,
                dkim_result=dkim_res,
                spf_result=spf_res,
                header_from=header_from,
            )
        )

    return DmarcReportSummary(
        org_name=org_name,
        report_id=report_id,
        domain=domain,
        total_messages=total_messages,
        passed_count=passed_count,
        failed_count=failed_count,
        records=records,
    )
