# LEVEL - Sistema di Gestione Palestra

Un'applicazione Django completa per la gestione di una palestra locale con sistema di check-in/check-out tramite QR code e integrazione con wallet digitali.

## 🏋️ Caratteristiche Principali

### Back-office (Django Admin)
- **Gestione Membri**: CRUD completo per utenti registrati
- **Campi Membri**: Nome, cognome, email, telefono, date abbonamento, tipo pagamento, numero ricevuta
- **Ricerca e Filtri**: Ricerca per nome, email, stato abbonamento
- **Visualizzazione QR**: Preview dei QR code generati automaticamente
- **Stato Abbonamento**: Indicatori colorati per abbonamenti attivi/scaduti
- **Gestione Accessi**: Tracciamento completo di check-in/check-out con stato abbonamento

### Front-end (Interfaccia Tablet)
- **Scansione QR**: Interfaccia touch-friendly per scansione QR code
- **Check-in/Check-out**: Pulsanti separati per le due operazioni
- **Messaggi Dinamici**: 
  - ✅ Verde: "Benvenuto, buon allenamento!" (QR valido + abbonamento attivo)
  - ❌ Rosso: "Abbonamento scaduto: non hai accesso." (QR valido + abbonamento scaduto)
  - ⚠️ Errore: "Utente non trovato" (QR non riconosciuto)
- **Auto-redirect**: Ritorno automatico alla home dopo 20 secondi
- **Modalità Kiosk**: Ottimizzata per tablet a schermo intero

### Wallet Digitali
- **Apple Wallet**: Generazione di .pkpass files
- **Google Wallet**: Integrazione con Google Pay API
- **Dettagli Pass**: Nome utente, validità abbonamento, logo palestra

## 🛠️ Tecnologie Utilizzate

- **Backend**: Django 5.2.3 (Python)
- **Database**: SQLite (locale)
- **Frontend**: Django Templates + Bootstrap 5 + Font Awesome
- **QR Code**: `qrcode` (generazione) + `html5-qrcode` (scansione)
- **Wallet**: `applepassgenerator` (Apple Wallet)
- **Immagini**: Pillow (PIL)
- **Validazione**: `python-dateutil`, `cryptography`

## 📦 Installazione

### Prerequisiti
- Python 3.11+
- pip
- Ambiente virtuale (raccomandato)

### Setup
```bash
# Clona il repository
git clone <repository-url>
cd LEVEL

# Crea ambiente virtuale
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installa dipendenze
pip install -r requirements.txt

# Configura database
python manage.py makemigrations
python manage.py migrate

# Crea superuser
python manage.py createsuperuser

# Avvia server
python manage.py runserver
```

## 🚀 Utilizzo

### Accesso Admin
- URL: `http://127.0.0.1:8000/admin/`
- Credenziali: quelle create con `createsuperuser`

### Interfaccia Tablet
- URL: `http://127.0.0.1:8000/`
- Modalità: Schermo intero su tablet

### Flusso Operativo
1. **Registrazione Membro**: Admin crea nuovo membro → QR generato automaticamente
2. **Check-in**: Membro scansiona QR → Sistema verifica abbonamento → Registra accesso
3. **Check-out**: Membro scansiona QR → Sistema registra uscita → Mostra messaggio di saluto

## 📊 Modelli Dati

### Member
```python
- id: AutoField (PK)
- uuid: CharField (36 chars, unique)
- first_name: CharField (100 chars)
- last_name: CharField (100 chars)
- email: EmailField (unique)
- phone: CharField (15 chars)
- subscription_start: DateField
- subscription_end: DateField
- qr_code_image: ImageField
- payment_type: CharField (choices: carta/contanti)
- receipt_number: CharField (50 chars)
- created_at: DateTimeField (auto_now_add)
- updated_at: DateTimeField (auto_now)
```

### CheckInOut
```python
- member: ForeignKey (Member)
- check_in: DateTimeField (auto_now_add)
- check_out: DateTimeField (null, blank)
- subscription_status: CharField (choices: attivo/scaduto)
```

## 🔧 Configurazione Wallet Pass

### Apple Wallet
1. **Certificati Richiesti**:
   - `pass.pem`: Certificato pass
   - `pass.key`: Chiave privata
   - `wwdr.pem`: Certificato WWDR

2. **Directory Struttura**:
   ```
   certificates/
   ├── pass.pem
   ├── pass.key
   └── wwdr.pem
   ```

3. **Immagini Richieste**:
   ```
   static/wallet/
   ├── icon.png (29x29)
   ├── icon@2x.png (58x58)
   ├── logo.png (160x50)
   └── logo@2x.png (320x100)
   ```

### Google Wallet
- Configurazione tramite Google Pay API
- Generazione di JSON per Smart Pass

## 📱 Funzionalità Avanzate

### Gestione Abbonamenti Scaduti
- **Registrazione Tentativi**: Anche accessi con abbonamento scaduto vengono registrati
- **Stato Colorato**: Indicatori visivi in admin per stato abbonamento
- **Messaggi Chiari**: Feedback immediato all'utente

### Statistiche e Report
- **Durata Sessioni**: Calcolo automatico tempo di permanenza
- **Frequenza Accessi**: Tracciamento pattern di utilizzo
- **Stato Abbonamenti**: Monitoraggio scadenze

### Sicurezza
- **UUID Unici**: Identificatori sicuri per ogni membro
- **Validazione Input**: Controlli su email, telefono, date
- **Log Accessi**: Tracciamento completo tentativi di accesso

## 🔄 Estensioni Future

- **Notifiche Email**: Avvisi scadenza abbonamenti
- **Multi-palestra**: Supporto per più sedi
- **API REST**: Integrazione con app mobile
- **Dashboard Analytics**: Statistiche avanzate
- **Sistema Pagamenti**: Integrazione gateway di pagamento

## 🐛 Risoluzione Problemi

### Errori Comuni
1. **ModuleNotFoundError**: Eseguire `pip install -r requirements.txt`
2. **Migrations**: Eseguire `python manage.py makemigrations && python manage.py migrate`
3. **Static Files**: Eseguire `python manage.py collectstatic`

### Debug
- **Log Django**: Controllare console per errori
- **Database**: Verificare migrazioni applicate
- **Media Files**: Controllare directory `media/`

## 📄 Licenza

Progetto didattico per apprendimento Django, QR code e integrazione wallet digitali.

## 👥 Contributi

Progetto sviluppato per scopi educativi e dimostrativi.

---

**LEVEL** - Gestione Palestra Intelligente 🏋️‍♂️ 