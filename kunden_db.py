import streamlit as st
import pandas as pd
from datetime import datetime
import os
import yaml
import streamlit_authenticator as stauth

# Login-Konfiguration
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

    # Datei-Pfade
    KUNDEN_DATEI = "data/kunden.csv"
    KOMMENTAR_DATEI = "data/kommentare.csv"

    ALLE_TAGS = ["LIT2Trade", "LIT-EA", "LIT-Signal", "Interessent", "gekauft"]
    ALLE_PRODUKTE = ["kein Produkt", "Expert-Advisor", "LIT2Trade"]
    ALLE_STATUS = ["interesse", "gekauft"]

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

    st.title("👤 Kundenmanagement Tool")

    kunden_df, kommentar_df = lade_daten()

    st.sidebar.header("📅 Neuen Kunden anlegen")
    with st.sidebar.form("neuer_kunde"):
        vorname = st.text_input("Vorname")
        nachname = st.text_input("Nachname")
        email = st.text_input("E-Mail")
        adresse = st.text_area("Adresse")
        erstgespraech = st.date_input("Erstgespräch")
        produkt = st.selectbox("Produkt", ALLE_PRODUKTE)
        status = st.selectbox("Status", ALLE_STATUS)
        tags = st.multiselect("Tags", ALLE_TAGS)

        bestelldatum = ""
        rechnung_geschickt = False
        rechnung_bezahlt = False
        zugang_digimember = False

        if status == "gekauft":
            bestelldatum = st.date_input("Bestelldatum")

        kommentar = st.text_area("Kommentar (optional)")
        submitted = st.form_submit_button("Speichern")

        if submitted and vorname and nachname and email:
            if not kunden_df[(kunden_df["Vorname"] == vorname) & (kunden_df["Nachname"] == nachname)].empty:
                st.warning("⚠️ Ein Kunde mit diesem Namen existiert bereits.")
            else:
                kunde = {
                    "Vorname": vorname,
                    "Nachname": nachname,
                    "E-Mail": email,
                    "Adresse": adresse,
                    "Produkt": produkt,
                    "Status": status,
                    "Tags": ";".join(tags),
                    "Konto ID1": "",
                    "Konto ID2": "",
                    "Konto ID3": "",
                    "Konto ID4": "",
                    "Bestelldatum": str(bestelldatum) if status == "gekauft" else "",
                    "Erstgespräch": str(erstgespraech),
                    "Rechnung geschickt": rechnung_geschickt,
                    "Rechnung bezahlt": rechnung_bezahlt,
                    "Zugang DigiMember": zugang_digimember
                }
                neue_id = speichere_kunde(kunde)
                if kommentar.strip():
                    speichere_kommentar(neue_id, kommentar.strip())
                st.success(f"Kunde {vorname} {nachname} wurde erfolgreich angelegt.")
                st.experimental_rerun()

    st.subheader("📋 Kundenübersicht")
    if not kunden_df.empty:
        cols = st.columns([3, 1])
        with cols[0]:
            for _, row in kunden_df.iterrows():
                with st.expander(f"{row['Vorname']} {row['Nachname']} – {row['Produkt']}"):
                    bearbeiten_button = st.button(f"Bearbeiten {row['ID']}")
                    if bearbeiten_button:
                        st.session_state[f"edit_{row['ID']}"] = not st.session_state.get(f"edit_{row['ID']}", False)

                    if st.session_state.get(f"edit_{row['ID']}", False):
                        with st.form(f"edit_form_{row['ID']}"):
                            vorname = st.text_input("Vorname", value=row["Vorname"])
                            nachname = st.text_input("Nachname", value=row["Nachname"])
                            email = st.text_input("E-Mail", value=row["E-Mail"])
                            adresse = st.text_area("Adresse", value=row["Adresse"])
                            erstgespraech = st.date_input("Erstgespräch", value=pd.to_datetime(row["Erstgespräch"]))
                            produkt = st.selectbox("Produkt", ALLE_PRODUKTE, index=ALLE_PRODUKTE.index(row["Produkt"]))
                            status = st.selectbox("Status", ALLE_STATUS, index=ALLE_STATUS.index(row["Status"]))
                            tags = st.multiselect("Tags", ALLE_TAGS, default=row["Tags"].split(";") if pd.notna(row["Tags"]) else [])

                            konto_ids = [st.text_input(f"Konto ID{i+1}", value=row[f"Konto ID{i+1}"]) for i in range(4)]

                            bestelldatum = ""
                            rechnung_geschickt = False
                            rechnung_bezahlt = False
                            zugang_digimember = False

                            if status == "gekauft":
                                bestelldatum = st.date_input("Bestelldatum", value=pd.to_datetime(row["Bestelldatum"]) if pd.notna(row["Bestelldatum"]) and row["Bestelldatum"] else datetime.today())
                                rechnung_geschickt = st.checkbox("Rechnung geschickt", value=row.get("Rechnung geschickt", False))
                                rechnung_bezahlt = st.checkbox("Rechnung bezahlt", value=row.get("Rechnung bezahlt", False))
                                zugang_digimember = st.checkbox("Zugang DigiMember angelegt", value=row.get("Zugang DigiMember", False))

                            kommentar_neu = st.text_area("Kommentar hinzufügen")

                            if st.form_submit_button("Speichern"):
                                kunde = {
                                    "Vorname": vorname,
                                    "Nachname": nachname,
                                    "E-Mail": email,
                                    "Adresse": adresse,
                                    "Produkt": produkt,
                                    "Status": status,
                                    "Tags": ";".join(tags),
                                    "Konto ID1": konto_ids[0],
                                    "Konto ID2": konto_ids[1],
                                    "Konto ID3": konto_ids[2],
                                    "Konto ID4": konto_ids[3],
                                    "Bestelldatum": str(bestelldatum) if status == "gekauft" else "",
                                    "Erstgespräch": str(erstgespraech),
                                    "Rechnung geschickt": rechnung_geschickt,
                                    "Rechnung bezahlt": rechnung_bezahlt,
                                    "Zugang DigiMember": zugang_digimember
                                }
                                speichere_kunde(kunde, kunden_id=row["ID"])
                                if kommentar_neu.strip():
                                    speichere_kommentar(row["ID"], kommentar_neu.strip())
                                st.success("Daten aktualisiert.")
                                st.experimental_rerun()
        with cols[1]:
            st.subheader("💬 Kommentare")
            for _, row in kunden_df.iterrows():
                kommentare = kommentar_df[kommentar_df["Kunden-ID"] == row["ID"]]
                if not kommentare.empty:
                    st.markdown(f"**{row['Vorname']} {row['Nachname']}**")
                    for _, komm in kommentare.sort_values("Datum", ascending=False).iterrows():
                        st.caption(f"{komm['Datum']}: {komm['Kommentar']}")
    else:
        st.info("❕ Noch keine Kunden vorhanden.")



    st.subheader("📋 Kundenübersicht")
    tag_filter = st.multiselect("🔎 Filter nach Tags", ALLE_TAGS)
    produkt_filter = st.multiselect("🔎 Filter nach Produkt", ALLE_PRODUKTE)

    gefiltert = kunden_df.copy()
    if tag_filter:
        gefiltert = gefiltert[gefiltert["Tags"].fillna("").str.contains("|".join(tag_filter))]
    if produkt_filter:
        gefiltert = gefiltert[gefiltert["Produkt"].isin(produkt_filter)]

    st.dataframe(gefiltert)

    st.subheader("✏️ Kundendaten bearbeiten")
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
                kunde_dict["Vorname"] = st.text_input("Vorname", value=kunde["Vorname"])
                kunde_dict["Nachname"] = st.text_input("Nachname", value=kunde["Nachname"])
                kunde_dict["E-Mail"] = st.text_input("E-Mail", value=kunde["E-Mail"])
                kunde_dict["Adresse"] = st.text_area("Adresse", value=kunde["Adresse"])
                kunde_dict["Erstgespräch"] = st.date_input("Erstgespräch", value=pd.to_datetime(kunde["Erstgespräch"]))
                kunde_dict["Produkt"] = st.selectbox("Produkt", ALLE_PRODUKTE, index=ALLE_PRODUKTE.index(kunde["Produkt"]))
                kunde_dict["Status"] = st.selectbox("Status", ALLE_STATUS, index=ALLE_STATUS.index(kunde["Status"]))
                kunde_dict["Tags"] = ";".join(st.multiselect("Tags", ALLE_TAGS, default=kunde["Tags"].split(";") if pd.notna(kunde["Tags"]) else []))

                if kunde_dict["Produkt"] == "Expert-Advisor":
                    kunde_dict["Konto ID1"] = st.text_input("Konto ID1", value=kunde["Konto ID1"])
                    kunde_dict["Konto ID2"] = st.text_input("Konto ID2", value=kunde["Konto ID2"])
                    kunde_dict["Konto ID3"] = st.text_input("Konto ID3", value=kunde["Konto ID3"])
                    kunde_dict["Konto ID4"] = st.text_input("Konto ID4", value=kunde["Konto ID4"])
                else:
                    kunde_dict["Konto ID1"] = kunde_dict["Konto ID2"] = kunde_dict["Konto ID3"] = kunde_dict["Konto ID4"] = ""

                if kunde_dict["Status"] == "gekauft":
                    kunde_dict["Bestelldatum"] = st.date_input("Bestelldatum", value=pd.to_datetime(kunde["Bestelldatum"]) if pd.notna(kunde["Bestelldatum"]) else datetime.today())
                    kunde_dict["Rechnung geschickt"] = st.checkbox("Rechnung geschickt", value=bool(kunde["Rechnung geschickt"]))
                    kunde_dict["Rechnung bezahlt"] = st.checkbox("Rechnung bezahlt", value=bool(kunde["Rechnung bezahlt"]))
                    kunde_dict["Zugang DigiMember"] = st.checkbox("Zugang DigiMember angelegt", value=bool(kunde["Zugang DigiMember"]))
                else:
                    kunde_dict["Bestelldatum"] = ""
                    kunde_dict["Rechnung geschickt"] = kunde_dict["Rechnung bezahlt"] = kunde_dict["Zugang DigiMember"] = False

                kommentar_neu = st.text_area("Neuen Kommentar hinzufügen")
                speichern = st.form_submit_button("Änderungen speichern")

                if speichern:
                    speichere_kunde(kunde_dict, kunden_id=ausgewählte_id)
                    if kommentar_neu.strip():
                        speichere_kommentar(ausgewählte_id, kommentar_neu.strip())
                    st.success("Änderungen gespeichert.")

            kommentare_kunde = kommentar_df[kommentar_df["Kunden-ID"] == ausgewählte_id]
            st.write("💬 Kommentare")
            st.write(kommentare_kunde.sort_values("Datum", ascending=False).reset_index(drop=True))

    else:
        st.info("❕ Noch keine Kunden vorhanden.")
