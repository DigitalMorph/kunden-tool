import pandas as pd
import os

if not os.path.exists("data"):
    os.makedirs("data")

df = pd.DataFrame(columns=[
    "ID", "Vorname", "Nachname", "E-Mail", "Adresse", "Produkt", "Status", "Tags",
    "Konto ID1", "Konto ID2", "Konto ID3", "Konto ID4", "Bestelldatum", "Erstgespräch",
    "Rechnung geschickt", "Rechnung bezahlt", "Zugang DigiMember"
])
df.to_csv("data/kunden.csv", index=False)

print("✅ Die Datei 'kunden.csv' wurde erfolgreich erstellt.")
