from typing import Protocol

from .main_types import Report


class ReportRepository(Protocol):
    def list(self) -> list[Report]: ...
    def add(self, report: Report) -> Report: ...
    def update(self, report: Report) -> Report: ...


class MemoryReportRepository:
    def __init__(self) -> None:
        self.items: list[Report] = []

    def list(self) -> list[Report]:
        return self.items

    def add(self, report: Report) -> Report:
        self.items.append(report)
        return report

    def update(self, report: Report) -> Report:
        for index, existing in enumerate(self.items):
            if existing.report_id == report.report_id:
                self.items[index] = report
                break
        return report


class SupabaseReportRepository:
    def __init__(self, url: str, key: str) -> None:
        from supabase import create_client
        self.client = create_client(url, key)

    def list(self) -> list[Report]:
        response = self.client.table("reports").select("*").execute()
        return [Report.model_validate(row) for row in (response.data or [])]

    def add(self, report: Report) -> Report:
        row = report.model_dump(mode="json")
        row["location"] = row.pop("location")
        self.client.table("reports").insert(row).execute()
        return report

    def update(self, report: Report) -> Report:
        self.client.table("reports").update(report.model_dump(mode="json")).eq(
            "report_id", report.report_id
        ).execute()
        return report
