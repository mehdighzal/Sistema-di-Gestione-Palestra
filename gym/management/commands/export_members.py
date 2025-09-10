import csv
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from gym.models import Member


def format_date(value: Optional[timezone.datetime.date]) -> str:
    if not value:
        return ""
    # Usa MM/DD/YYYY per coerenza con gli esempi del CSV
    return value.strftime("%m/%d/%Y")


class Command(BaseCommand):
    help = "Esporta i membri in un file CSV usando le stesse colonne dell'import."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            required=True,
            help="Percorso del file CSV di output",
        )
        parser.add_argument(
            "--delimiter",
            default=",",
            help="Delimitatore CSV (default: ,)",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"])
        delimiter = options["delimiter"]

        # Intestazioni coerenti con l'importatore
        headers = [
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

        try:
            # Crea directory se necessario
            if output_path.parent and not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
                writer.writeheader()

                for member in Member.objects.all().order_by("last_name", "first_name"):
                    writer.writerow(
                        {
                            "first_name": member.first_name or "",
                            "last_name": member.last_name or "",
                            "email": member.email or "",
                            "phone": member.phone or "",
                            "subscription_start": format_date(member.subscription_start),
                            "subscription_end": format_date(member.subscription_end),
                            "medical_certificate_start": format_date(member.medical_certificate_start),
                            "medical_certificate_end": format_date(member.medical_certificate_end),
                            "payment_type": member.payment_type or "",
                            "receipt_number": member.receipt_number or "",
                            "registration_fee_paid_until": format_date(member.registration_fee_paid_until),
                        }
                    )

        except Exception as exc:
            raise CommandError(f"Errore durante l'esportazione: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Esportazione completata: {output_path}"))


