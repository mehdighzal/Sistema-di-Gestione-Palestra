import csv
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dateutil import parser as dateparser

from gym.models import Member


def parse_date(value: str) -> Optional[timezone.datetime.date]:
    if not value:
        return None
    value = str(value).strip()
    if not value or value.lower() in {"none", "null", "nan"}:
        return None
    try:
        # dateutil handles many formats e.g. 2025-01-31, 31/01/2025, 31-01-2025
        return dateparser.parse(value, dayfirst=True).date()
    except Exception:
        raise


class Command(BaseCommand):
    help = (
        "Importa membri da un file CSV (esporta Excel in CSV). "
        "Richiede intestazioni: first_name,last_name,phone,subscription_start,subscription_end "
        "(email è opzionale - se mancante viene generata automaticamente). "
        "Opzionali: medical_certificate_start,medical_certificate_end,payment_type,receipt_number,registration_fee_paid_until"
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Percorso al file CSV")
        parser.add_argument(
            "--delimiter",
            default=",",
            help="Delimitatore CSV (default: ,)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra cosa verrebbe importato senza salvare",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        delimiter = options["delimiter"]
        dry_run = options["dry_run"]

        if not csv_path.exists():
            raise CommandError(f"File non trovato: {csv_path}")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            required = {"first_name", "last_name", "phone", "subscription_start", "subscription_end"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise CommandError(f"Colonne mancanti nel CSV: {', '.join(sorted(missing))}")

            for idx, row in enumerate(reader, start=2):  # start=2 to account for header line
                try:
                    first_name = (row.get("first_name") or "").strip()
                    last_name = (row.get("last_name") or "").strip()
                    email = (row.get("email") or "").strip().lower()
                    
                    if not first_name or not last_name:
                        self.stdout.write(self.style.WARNING(f"Riga {idx}: nome o cognome mancante → salto"))
                        skipped_count += 1
                        continue
                    
                    # Generate a placeholder email if missing
                    if not email:
                        email = f"{first_name.lower()}.{last_name.lower()}@placeholder.local"

                    # Set default subscription dates if missing
                    today = timezone.now().date()
                    subscription_start = parse_date(row.get("subscription_start") or "")
                    subscription_end = parse_date(row.get("subscription_end") or "")
                    
                    # If subscription dates are missing, set defaults
                    if not subscription_start:
                        subscription_start = today
                    if not subscription_end:
                        subscription_end = today.replace(year=today.year + 1)  # 1 year from today
                    
                    defaults = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": (row.get("phone") or "").strip(),
                        "subscription_start": subscription_start,
                        "subscription_end": subscription_end,
                        "medical_certificate_start": parse_date(row.get("medical_certificate_start") or ""),
                        "medical_certificate_end": parse_date(row.get("medical_certificate_end") or ""),
                        "payment_type": (row.get("payment_type") or "carta").strip() or "carta",
                        "receipt_number": (row.get("receipt_number") or "").strip(),
                        "registration_fee_paid_until": parse_date(row.get("registration_fee_paid_until") or ""),
                    }

                    member, created = Member.objects.update_or_create(
                        email=email,
                        defaults=defaults,
                    )

                    if dry_run:
                        action = "CREEREI" if created else "AGGIORNEREI"
                        email_display = email if "@placeholder.local" not in email else "SENZA EMAIL"
                        self.stdout.write(f"{action} {member.first_name} {member.last_name} <{email_display}>")
                        # Do not count in dry-run
                        continue

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as exc:
                    skipped_count += 1
                    self.stderr.write(self.style.ERROR(f"Riga {idx}: errore {exc}"))

        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry-run completato. Nessun dato salvato."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Import completato. Creati: {created_count}, Aggiornati: {updated_count}, Saltati: {skipped_count}"
            ))


