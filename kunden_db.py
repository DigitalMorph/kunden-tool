import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from datetime import datetime
import os
import yaml
import shutil
import streamlit_authenticator as stauth

# === DATEIPFADE ===
KUNDEN_DATEI = "data/kunden.csv"
KOMMENTAR_DATEI = "data/kommentare.csv"
LOG_DATEI = "data/logs.csv"
BACKUP_ORDNER = "backup"

# === BACKUP-FUNKTION ===
def sichere_backup(dateipfad):
    if not os.path.exists(BACKUP_ORDNER):
        os.makedirs(BACKUP_ORDNER)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dateiname = os.path.basename(dateipfad).replace(".csv", f"_backup_{timestamp}.csv")
    shutil.copyfile(dateipfad, os.path.join(BACKUP_ORDNER, dateiname))

# === LOGIN ===
with open("config.yaml") as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status is False:
    st.error("Benutzername oder Passwort ist falsch.")
elif authentication_status is None:
    st.warning("Bitte einloggen.")
else:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Eingeloggt als {name}")

    # === INITIALISIERUNG ===
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.isfile(KUNDEN_DATEI):
        pd.DataFrame(columns=["ID", "Vorname", "Nachname", "E-Mail", "Adresse", "Produkt", "Status", "Tags", "Konto ID1", "Konto ID2", "Konto ID3", "Konto ID4", "Bestelldatum", "Erstgespräch", "Rechnung geschickt", "Rechnung bezahlt", "Zugang DigiMember"]).to_csv(KUNDEN_DATEI, index=False)
    if not os.path.isfile(KOMMENTAR_DATEI):
        pd.DataFrame(columns=["Kunden-ID", "Datum", "Kommentar"]).to_csv(KOMMENTAR_DATEI, index=False)
    if not os.path.isfile(LOG_DATEI):
        pd.DataFrame(columns=["Datum", "Benutzer", "Aktion", "Kunden-ID", "Details"]).to_csv(LOG_DATEI, index=False)

    kunden_df = pd.read_csv(KUNDEN_DATEI)
    kommentar_df = pd.read_csv(KOMMENTAR_DATEI)

    def speichere_kunde(kunde, kunden_id=None):
        df = pd.read_csv(KUNDEN_DATEI)
        if kunden_id:
            df.loc[df["ID"] == kunden_id, list(kunde.keys())] = list(kunde.values())
            neue_id = kunden_id
        else:
            neue_id = df["ID"].max() + 1 if not df.empty else 1
            kunde["ID"] = neue_id
            df = pd.concat([df, pd.DataFrame([kunde])])
        df.to_csv(KUNDEN_DATEI, index=False)
        sichere_backup(KUNDEN_DATEI)
        return neue_id

    def speichere_kommentar(kunden_id, kommentar_text):
        df = pd.read_csv(KOMMENTAR_DATEI)
        neuer_kommentar = {"Kunden-ID": kunden_id, "Datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Kommentar": kommentar_text}
        df = pd.concat([df, pd.DataFrame([neuer_kommentar])])
        df.to_csv(KOMMENTAR_DATEI, index=False)
        sichere_backup(KOMMENTAR_DATEI)

    def log_aktion(aktion, kunden_id, details=""):
        df = pd.read_csv(LOG_DATEI)
        neuer_log = {"Datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Benutzer": name, "Aktion": aktion, "Kunden-ID": kunden_id, "Details": details}
        df = pd.concat([df, pd.DataFrame([neuer_log])])
        df.to_csv(LOG_DATEI, index=False)
        sichere_backup(LOG_DATEI)

    st.title("👤 Kundenmanagement Tool")

    st.subheader("➕ Neuen Kunden anlegen")
    with st.form("neukunde_form"):
        vorname = st.text_input("Vorname")
        nachname = st.text_input("Nachname")
        email = st.text_input("E-Mail")
        adresse = st.text_area("Adresse")
        produkt = st.selectbox("Produkt", ["kein Produkt", "Expert-Advisor", "LIT2Trade"])
        status = st.selectbox("Status", ["Interesse", "Kauf"])
        tags = st.text_input("Tags (durch Semikolon getrennt)")
        kommentar = st.text_area("Kommentar")
        submitted = st.form_submit_button("Speichern")

        if submitted and vorname and nachname and email:
            kunde = {
                "Vorname": vorname,
                "Nachname": nachname,
                "E-Mail": email,
                "Adresse": adresse,
                "Produkt": produkt,
                "Status": status,
                "Tags": tags,
                "Konto ID1": "",
                "Konto ID2": "",
                "Konto ID3": "",
                "Konto ID4": "",
                "Bestelldatum": "",
                "Erstgespräch": "",
                "Rechnung geschickt": False,
                "Rechnung bezahlt": False,
                "Zugang DigiMember": False
            }
            neue_id = speichere_kunde(kunde)
            if kommentar.strip():
                speichere_kommentar(neue_id, kommentar.strip())
            log_aktion("Neu angelegt", neue_id, f"{vorname} {nachname}")
            st.success("Kunde gespeichert.")
            st.experimental_rerun()

    st.subheader("📄 Kundendaten bearbeiten")
    if not kunden_df.empty:
        kunde_auswahl = st.selectbox("Kunden-ID auswählen", kunden_df["ID"].astype(str) + " – " + kunden_df["Vorname"] + " " + kunden_df["Nachname"])
        if kunde_auswahl:
            ausgewählte_id = int(kunde_auswahl.split("–")[0].strip())
            kunde = kunden_df[kunden_df["ID"] == ausgewählte_id].iloc[0]

            with st.form("bearbeiten_form"):
                kunde_dict = {}
                for feld in ["Vorname", "Nachname", "E-Mail", "Adresse", "Produkt", "Status"]:
                    kunde_dict[feld] = st.text_input(feld, value=str(kunde[feld]))
                kommentar_neu = st.text_area("Neuen Kommentar hinzufügen")
                speichern = st.form_submit_button("Speichern")

                if speichern:
                    aenderungen = []
                    for key in kunde_dict:
                        alt = str(kunde[key]) if key in kunde else ""
                        neu = str(kunde_dict[key])
                        if alt != neu:
                            aenderungen.append(f"{key}: '{alt}' → '{neu}'")
                    aenderungs_text = "; ".join(aenderungen) if aenderungen else "Keine Änderungen"

                    speichere_kunde(kunde_dict, kunden_id=ausgewählte_id)
                    if kommentar_neu.strip():
                        speichere_kommentar(ausgewählte_id, kommentar_neu.strip())
                    log_aktion("Bearbeitet", ausgewählte_id, aenderungs_text)
                    st.success("Kunde aktualisiert.")
                    st.experimental_rerun()

    st.subheader("📊 Änderungsprotokoll")
    if os.path.isfile(LOG_DATEI):
        logs = pd.read_csv(LOG_DATEI).sort_values("Datum", ascending=False)
        st.dataframe(logs)

    st.subheader("⬇️ Backup herunterladen")
    with open(KUNDEN_DATEI, "rb") as f:
        st.download_button("📁 Kunden.csv herunterladen", f, file_name="kunden.csv")
    with open(KOMMENTAR_DATEI, "rb") as f:
        st.download_button("📁 Kommentare.csv herunterladen", f, file_name="kommentare.csv")
    with open(LOG_DATEI, "rb") as f:
        st.download_button("📁 Logs.csv herunterladen", f, file_name="logs.csv")
