import gspread, json, os

JSON_FILE = "google-credential.json"

# 1) Mostra quale service account stiamo usando (legge il JSON)
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
sa_email = data.get("client_email")
print("== Service Account in uso ==")
print(sa_email)

# 2) Autentica con gli scope giusti
gc = gspread.service_account(filename=JSON_FILE)

# 3) Elenca i fogli che il service account *vede*
print("\n== Fogli visibili dal service account (max 20) ==")
files = gc.list_spreadsheet_files()
for f in files[:20]:
    print(f"- {f['name']}  (id={f['id']})")

# 4) PROVA: apri per ID (metti qui l'ID ESATTO del tuo foglio)
SPREADSHEET_ID = "1AAsiBuHBbKILRHkDM9E1SMEl061iAmPyF5NV94ncO80"  # <-- ricopia dal tuo URL /d/ID/...
print("\n== Apro per ID ==")
sh = gc.open_by_key(SPREADSHEET_ID)   # se qui esplode: ID errato oppure non condiviso a questo SA
ws = sh.sheet1
ws.update("A1", [["Ciao, funziona! 🚀"]])
print("OK: scritto in A1")






