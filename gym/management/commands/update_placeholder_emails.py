import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from gym.models import Member


class Command(BaseCommand):
    help = (
        "Aggiorna le email placeholder (@placeholder.local) con email reali da un file CSV. "
        "Il CSV deve avere le colonne: first_name,last_name,email"
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Percorso del file CSV con le email reali")
        parser.add_argument(
            "--delimiter",
            default=",",
            help="Delimitatore delle colonne nel CSV (default: ,)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula l'aggiornamento mostrando le azioni senza salvare i dati.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        delimiter = options["delimiter"]
        dry_run = options["dry_run"]

        if not csv_path.exists():
            raise CommandError(f"File non trovato: {csv_path}")

        updated_count = 0
        not_found_count = 0
        skipped_count = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Normalizza i nomi delle colonne
            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]

            required = {"first_name", "last_name", "email"}
            if not required.issubset(set(reader.fieldnames)):
                missing = required - set(reader.fieldnames)
                raise CommandError(f"Colonne obbligatorie mancanti nel CSV: {', '.join(sorted(missing))}")

            for idx, row in enumerate(reader, start=2):
                try:
                    first_name = (row.get("first_name") or "").strip()
                    last_name = (row.get("last_name") or "").strip()
                    new_email = (row.get("email") or "").strip().lower()

                    if not first_name or not last_name or not new_email:
                        self.stdout.write(self.style.WARNING(f"Riga {idx}: Dati mancanti -> Salto."))
                        skipped_count += 1
                        continue

                    # Cerca il membro per nome e cognome
                    try:
                        member = Member.objects.get(
                            first_name__iexact=first_name, 
                            last_name__iexact=last_name
                        )
                    except Member.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Riga {idx}: Membro '{first_name} {last_name}' non trovato -> Salto."))
                        not_found_count += 1
                        continue
                    except Member.MultipleObjectsReturned:
                        self.stdout.write(self.style.WARNING(f"Riga {idx}: Trovati membri multipli per '{first_name} {last_name}' -> Salto."))
                        skipped_count += 1
                        continue

                    # Verifica se ha email placeholder
                    if "@placeholder.local" not in member.email:
                        self.stdout.write(self.style.WARNING(f"Riga {idx}: '{first_name} {last_name}' ha già email reale ({member.email}) -> Salto."))
                        skipped_count += 1
                        continue

                    # Verifica se la nuova email è già in uso
                    if Member.objects.filter(email__iexact=new_email).exclude(pk=member.pk).exists():
                        self.stdout.write(self.style.WARNING(f"Riga {idx}: Email '{new_email}' già in uso da altro membro -> Salto."))
                        skipped_count += 1
                        continue

                    if dry_run:
                        self.stdout.write(f"AGGIORNEREI {first_name} {last_name}: {member.email} -> {new_email}")
                        continue

                    # Aggiorna l'email
                    old_email = member.email
                    member.email = new_email
                    member.save()
                    
                    self.stdout.write(f"Aggiornato {first_name} {last_name}: {old_email} -> {new_email}")
                    updated_count += 1

                except Exception as exc:
                    self.stderr.write(self.style.ERROR(f"Riga {idx}: Errore '{exc}' -> Salto."))
                    skipped_count += 1

        if dry_run:
            self.stdout.write(self.style.NOTICE("\nDry-run completato. Nessun dato è stato salvato."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nAggiornamento completato. Aggiornati: {updated_count}, Non trovati: {not_found_count}, Saltati: {skipped_count}"
            ))
