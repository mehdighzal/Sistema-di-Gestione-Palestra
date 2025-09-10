import csv
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils import timezone
from dateutil import parser as dateparser

from gym.models import Member


def parse_date(value: str) -> Optional[timezone.datetime.date]:
    """Converte una stringa in un oggetto data, gestendo vari formati."""
    if not value:
        return None
    value = str(value).strip()
    if not value or value.lower() in {"none", "null", "nan", "#value!"}:
        return None
    
    # Rimuovi suffissi come "CA" o "CC" se presenti
    value = value.replace("CA", "").replace("CC", "").strip()
    
    try:
        # Prova prima con dayfirst=True (formato italiano: giorno/mese/anno)
        parsed = dateparser.parse(value, dayfirst=True)
        if parsed:
            return parsed.date()
        
        # Se fallisce, prova con dayfirst=False (formato americano: mese/giorno/anno)
        parsed = dateparser.parse(value, dayfirst=False)
        if parsed:
            return parsed.date()
            
        return None
    except (dateparser.ParserError, TypeError):
        # Ignora le date non valide e restituisce None
        return None


class Command(BaseCommand):
    help = (
        "Importa o aggiorna membri da un file CSV. "
        "Cerca per email, se assente, cerca per nome e cognome."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Percorso del file CSV da importare")
        parser.add_argument(
            "--delimiter",
            default=",",
            help="Delimitatore delle colonne nel CSV (default: ,)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula l'importazione mostrando le azioni senza salvare i dati.",
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
            
            # Normalizza i nomi delle colonne (rimuove spazi e converte in minuscolo)
            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]

            required = {"first_name", "last_name"}
            if not required.issubset(set(reader.fieldnames)):
                missing = required - set(reader.fieldnames)
                raise CommandError(f"Colonne obbligatorie mancanti nel CSV: {', '.join(sorted(missing))}")

            for idx, row in enumerate(reader, start=2):
                try:
                    first_name = (row.get("first_name") or "").strip()
                    last_name = (row.get("last_name") or "").strip()
                    email = (row.get("email") or "").strip().lower()

                    if not first_name or not last_name:
                        self.stdout.write(self.style.WARNING(f"Riga {idx}: Nome o cognome mancante -> Salto."))
                        skipped_count += 1
                        continue

                    # *** LOGICA DI RICERCA MIGLIORATA ***
                    member = None
                    if email:
                        try:
                            member = Member.objects.get(email__iexact=email)
                        except Member.DoesNotExist:
                            pass

                    if not member:
                        try:
                            member = Member.objects.get(first_name__iexact=first_name, last_name__iexact=last_name)
                        except Member.DoesNotExist:
                            pass
                        except Member.MultipleObjectsReturned:
                            self.stdout.write(self.style.WARNING(
                                f"Riga {idx}: Trovati membri multipli per '{first_name} {last_name}'. -> Salto per sicurezza."
                            ))
                            skipped_count += 1
                            continue
                    
                    # *** CORREZIONE PER ERRORE NOT NULL ***
                    today = parse_date("01/01/2025")
                    subscription_start = parse_date(row.get("subscription_start"))
                    subscription_end = parse_date(row.get("subscription_end"))
                    
                    if not subscription_start:
                        subscription_start = today
                    if not subscription_end:
                        # Se subscription_end è vuoto, calcola un mese dopo subscription_start
                        if subscription_start:
                            from dateutil.relativedelta import relativedelta
                            subscription_end = subscription_start + relativedelta(months=1)
                        else:
                            subscription_end = today + relativedelta(months=1)

                    data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": (row.get("phone") or "").strip(),
                        "subscription_start": subscription_start,
                        "subscription_end": subscription_end,
                        "medical_certificate_start": parse_date(row.get("medical_certificate_start")),
                        "medical_certificate_end": parse_date(row.get("medical_certificate_end")),
                        "payment_type": (row.get("payment_type") or "non specificato").strip(),
                        "receipt_number": (row.get("receipt_number") or "").strip(),
                        "registration_fee_paid_until": parse_date(row.get("registration_fee_paid_until")),
                    }
                    
                    if email:
                        data["email"] = email
                    else:
                        # Generate unique placeholder email for members without email
                        base_email = f"{first_name.lower()}.{last_name.lower()}@placeholder.local"
                        placeholder_email = base_email
                        counter = 1
                        # Ensure unique email by adding counter if needed
                        while Member.objects.filter(email__iexact=placeholder_email).exists():
                            placeholder_email = f"{first_name.lower()}.{last_name.lower()}{counter}@placeholder.local"
                            counter += 1
                        data["email"] = placeholder_email

                    if dry_run:
                        action = "CREEREI" if not member else "AGGIORNEREI"
                        email_display = email if email else "SENZA EMAIL"
                        self.stdout.write(f"{action} {first_name} {last_name} <{email_display}>")
                        continue

                    if member:
                        # AGGIORNA MEMBRO ESISTENTE
                        Member.objects.filter(pk=member.pk).update(**data)
                        updated_count += 1
                    else:
                        # CREA NUOVO MEMBRO
                        Member.objects.create(**data)
                        created_count += 1

                except IntegrityError as exc:
                    # *** GESTIONE ERRORI MIGLIORATA ***
                    error_message = str(exc).lower()
                    style = self.style.WARNING
                    if "unique constraint failed" in error_message and "email" in error_message:
                        message = f"L'email '{email}' è già in uso da un altro membro."
                    elif "not null constraint failed" in error_message:
                        message = f"Dati obbligatori mancanti (es. date abbonamento)."
                    else:
                        message = f"Errore di integrità: {exc}"
                        style = self.style.ERROR
                    
                    self.stdout.write(style(f"Riga {idx}: {message} -> Salto."))
                    skipped_count += 1
                except Exception as exc:
                    self.stderr.write(self.style.ERROR(f"Riga {idx}: Errore inaspettato '{exc}' -> Salto."))
                    skipped_count += 1

        if dry_run:
            self.stdout.write(self.style.NOTICE("\nDry-run completato. Nessun dato è stato salvato."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nImportazione completata. Creati: {created_count}, Aggiornati: {updated_count}, Saltati: {skipped_count}"
            ))

