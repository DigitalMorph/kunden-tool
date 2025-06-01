import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from datetime import datetime
import os
import yaml
import shutil
import streamlit_authenticator as stauth

# 📁 Backup-Funktion
def sichere_backup(datei):
    backup_dir = "backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ziel = os.path.join(backup_dir, os.path.basename(datei).replace(".csv", f"_backup_{timestamp}.csv"))
    shutil.copyfile(datei, ziel)

# 🔐 Login-Konfiguration
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
if authentication_status is None:
    st.warning("Bitte einloggen.")
if authentication_status:

    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Eingeloggt als {name}")

    # 📄 Datei-Pfade
    KUNDEN_DATEI = "data/kunden.csv"
    KOMMENTAR_DATEI = "data/kommentare.csv"
    LOG_DATEI = "data/logs.csv"

    def lade_daten():
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.isfile(KUNDEN_DATEI):
            pd.DataFrame(columns=[
                "ID", "Vorname", "Nachname", "E-Mail", "Adresse", "Produkt", "Status", "Tags",
                "Konto ID1", "Konto ID2", "Konto ID3", "Konto ID4", "Bestelldatum", "Erstgespräch",
                "Rechnung geschickt", "Rechnung bezahlt", "Zugang DigiMember"
            ]).to_csv(KUNDEN_DATEI, index=False)
        if not os.path.isfile(KOMMENTAR_DATEI):
            pd.DataFrame(columns=["Kunden-ID", "Datum", "Kommentar"]).to_csv(KOMMENTAR_DATEI, index=False)
        if not os.path.isfile(LOG_DATEI):
            pd.DataFrame(columns=["Datum", "Benutzer", "Aktion", "Kunden-ID", "Details"]).to_csv(LOG_DATEI, index=False)
        return pd.read_csv(KUNDEN_DATEI), pd.read_csv(KOMMENTAR_DATEI)

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
        neuer_kommentar = {
            "Kunden-ID": kunden_id,
            "Datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Kommentar": kommentar_text
        }
        df = pd.concat([df, pd.DataFrame([neuer_kommentar])])
        df.to_csv(KOMMENTAR_DATEI, index=False)
        sichere_backup(KOMMENTAR_DATEI)

    def log_aktion(aktion, kunden_id, details=""):
        df = pd.read_csv(LOG_DATEI)
        neuer_log = {
            "Datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Benutzer": name,
            "Aktion": aktion,
            "Kunden-ID": kunden_id,
            "Details": details
        }
        df = pd.concat([df, pd.DataFrame([neuer_log])])
        df.to_csv(LOG_DATEI, index=False)
        sichere_backup(LOG_DATEI)

    st.title("👤 Kundenmanagement Tool")

    kunden_df, kommentar_df = lade_daten()

    st.subheader("📄 Kundendaten bearbeiten")

    if not kunden_df.empty:
        bearbeite_kunde = st.selectbox(
            "Kunden-ID auswählen",
            kunden_df["ID"].astype(str) + " – " + kunden_df["Vorname"] + " " + kunden_df["Nachname"]
        )

        if bearbeite_kunde:
            ausgewählte_id = int(bearbeite_kunde.split("–")[0].strip())
            kunde = kunden_df[kunden_df["ID"] == ausgewählte_id].iloc[0]
            with st.form("kunde_bearbeiten"):
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
                    st.success("Kunde wurde aktualisiert.")
                    st.experimental_rerun()

    st.subheader("📊 Änderungsprotokoll")
    try:
        log_df = pd.read_csv(LOG_DATEI)
        log_df = log_df.sort_values("Datum", ascending=False).reset_index(drop=True)
        st.dataframe(log_df)
    except:
        st.info("Keine Logs gefunden.")

    st.subheader("⬇️ Backup herunterladen")
    with open(KUNDEN_DATEI, "rb") as f:
        st.download_button("📁 Kunden.csv herunterladen", f, file_name="kunden.csv")
    with open(KOMMENTAR_DATEI, "rb") as f:
        st.download_button("📁 Kommentare.csv herunterladen", f, file_name="kommentare.csv")
    with open(LOG_DATEI, "rb") as f:
        st.download_button("📁 Logs.csv herunterladen", f, file_name="logs.csv")
