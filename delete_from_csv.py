import os
import django
import csv

# --- Imposta Django ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# --- Importa il modello da cui vuoi cancellare ---
from gym.models import Member  # sostituisci con il tuo modello reale

# --- Percorso del CSV ---
csv_file_path = 'your_file.csv'

# --- Leggi i dati dal CSV e cancella ---
with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        first_name = row['first_name']
        last_name = row['last_name']
        deleted, _ = Member.objects.filter(first_name=first_name, last_name=last_name).delete()
        if deleted:
            print(f"Cancellato: {first_name} {last_name}")
        else:
            print(f"Non trovato: {first_name} {last_name}")

print("Cancellazione completata.")
