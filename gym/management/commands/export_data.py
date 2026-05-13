import csv
from pathlib import Path
from typing import List, Dict

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from gym.models import Member, SalaMember


def format_date(value) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d")


COMMON_HEADERS: List[str] = [
    "first_name",
    "last_name",
    "email",
    "phone",
    "subscription_start",
    "subscription_end",
    "medical_certificate_start",
    "medical_certificate_end",
    "payment_type",
    "receipt_number",
    "registration_fee_paid_until",
]


def row_from_instance(obj) -> Dict[str, str]:
    return {
        "first_name": obj.first_name or "",
        "last_name": obj.last_name or "",
        "email": obj.email or "",
        "phone": obj.phone or "",
        "subscription_start": format_date(obj.subscription_start),
        "subscription_end": format_date(obj.subscription_end),
        "medical_certificate_start": format_date(obj.medical_certificate_start),
        "medical_certificate_end": format_date(obj.medical_certificate_end),
        "payment_type": obj.payment_type or "",
        "receipt_number": obj.receipt_number or "",
        "registration_fee_paid_until": format_date(obj.registration_fee_paid_until),
    }


class Command(BaseCommand):
    help = (
        "Export Members or SalaMembers to CSV or XLSX. "
        "Examples: \n"
        "  python manage.py export_data --entity members --format csv --output exports/members.csv\n"
        "  python manage.py export_data --entity sala --format xlsx --output exports/sala.xlsx\n"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity",
            choices=["members", "sala"],
            required=True,
            help="Which dataset to export: members (Member) or sala (SalaMember)",
        )
        parser.add_argument(
            "--format",
            choices=["csv", "xlsx"],
            default="csv",
            help="Output format",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            help="Output file path. If omitted, a timestamped filename will be used in ./exports/",
        )
        parser.add_argument(
            "--delimiter",
            default=",",
            help="CSV delimiter (only for csv format)",
        )

    def handle(self, *args, **options):
        entity = options["entity"]
        output_format = options["format"].lower()
        delimiter = options["delimiter"]

        if not options.get("output"):
            ts = timezone.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"{entity}_{ts}.{output_format}"
            output_path = Path("exports") / default_name
        else:
            output_path = Path(options["output"]).resolve()

        # Select queryset and label
        if entity == "members":
            queryset = Member.objects.all().order_by("last_name", "first_name")
        else:  # sala
            queryset = SalaMember.objects.all().order_by("last_name", "first_name")

        # Ensure parent directory exists
        if output_path.parent and not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if output_format == "csv":
                self._export_csv(output_path, queryset, delimiter)
            else:
                self._export_xlsx(output_path, queryset)
        except Exception as exc:
            raise CommandError(f"Errore durante l'esportazione: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Esportazione completata: {output_path}"))

    def _export_csv(self, output_path: Path, queryset, delimiter: str):
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COMMON_HEADERS, delimiter=delimiter)
            writer.writeheader()
            for obj in queryset:
                writer.writerow(row_from_instance(obj))

    def _export_xlsx(self, output_path: Path, queryset):
        try:
            from openpyxl import Workbook
        except ImportError as exc:
            raise CommandError(
                "openpyxl non è installato. Aggiungi 'openpyxl' a requirements.txt e installa le dipendenze."
            ) from exc

        wb = Workbook()
        ws = wb.active
        ws.title = "Export"

        # Headers
        ws.append(COMMON_HEADERS)

        # Rows
        for obj in queryset:
            row = row_from_instance(obj)
            ws.append([row[h] for h in COMMON_HEADERS])

        wb.save(str(output_path))


