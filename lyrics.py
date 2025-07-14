import streamlit as st
import pandas as pd
import gspread
import requests
from google.oauth2.service_account import Credentials

# --- CONFIG ---
SHEET_ID = "1xDkePn-ka6xvfoInEGe0PRWLPd39j7fhigQNEpOFkDw"
WORKSHEET_NAME1 = "lyrics"
WORKSHEET_NAME2 = "members"
WORKSHEET_NAME3 = "videos"
WORKSHEET_NAME4 = "performances"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# --- GOOGLE SHEETS SETUP ---
@st.cache_resource
def get_worksheets():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    songs_ws = sheet.worksheet(WORKSHEET_NAME1)
    members_ws = sheet.worksheet(WORKSHEET_NAME2)
    videos_ws = sheet.worksheet(WORKSHEET_NAME3)
    performance_ws = sheet.worksheet(WORKSHEET_NAME4)
    return songs_ws, members_ws, videos_ws, performance_ws

def get_lyrics_df(ws):
    data = ws.get_all_records()
    return pd.DataFrame(data)

def add_new_song(ws, title, artist, lyrics):
    ws.append_row([title.strip(), artist.strip(), lyrics.strip()])

def load_members(ws):
    df = pd.DataFrame(ws.get_all_records())
    return df.to_dict(orient="records")

def load_videos(ws):
    df = pd.DataFrame(ws.get_all_records())
    return df.to_dict(orient="records")
    
def load_performances(ws):
    df = pd.DataFrame(ws.get_all_records())
    return df.to_dict(orient="records")


def search_lyrics_online(artist, title):
    try:
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        res = requests.get(url)
        if res.status_code == 200:
            return res.json().get('lyrics', 'Lyrics not found.')
        else:
            return "Lyrics not found online."
    except:
        return "Error fetching lyrics."



# --- CUSTOM STYLES ---
st.markdown("""
    <style>
    .lyrics-box {
        background-color: #fffbe6;
        padding: 20px;
        border-radius: 10px;
        font-size: 24px;
        font-family: 'Courier New', monospace;
        color: black;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    @media screen and (max-width: 600px) {
        .lyrics-box {
            font-size: 20px;
        }
    }
    </style>
""", unsafe_allow_html=True)
# --- STREAMLIT UI ---
st.set_page_config(page_title="🎤 SIBuskerz Lyrics App", layout="wide")
st.sidebar.image("SIBuskerz.JPG", use_container_width=True)

st.title("🎶 SIBuskerz Lyrics Performance©")

menu = [
    "📍 Performance Venues & Tokens",
    "📖 View Lyrics/Lihat Lirik",
    "➕ Add New Song/Masukkan lirik Lagu baru",
    "🌐 Search Lyrics Online",
    "👥 Meet The Members",
    "🎤 Performance Mode"
    
]

choice = st.sidebar.selectbox("Navigation", menu)

worksheet, members_sheet, videos_sheet, performances_sheet = get_worksheets()
lyrics_df = get_lyrics_df(worksheet)

# --- VIEW LYRICS ---
if choice == "📖 View Lyrics/Lihat Lirik":
   
    st.subheader("Select a song to view lyrics")

    lyrics_df_sorted = lyrics_df.sort_values(by='Title')
    full_titles = lyrics_df_sorted['Title'] + " - " + lyrics_df_sorted['Artist']

    search_term = st.text_input("🔍 Search song title")
    filtered_titles = [title for title in full_titles if search_term.lower() in title.lower()]

    selection = st.selectbox("Song List", filtered_titles if search_term else full_titles)

    if selection:
        title, artist = selection.split(" - ")
        row = lyrics_df_sorted[(lyrics_df_sorted['Title'] == title) & (lyrics_df_sorted['Artist'] == artist)].iloc[0]
        st.markdown(f"### 🎵 {row['Title']} by {row['Artist']}")
        st.markdown(f"""
        <div class="lyrics-box">
            <pre>{row['Lyrics']}</pre>
        </div>
        """, unsafe_allow_html=True)

# --- ADD NEW SONG ---
elif choice == "➕ Add New Song/Masukkan lirik Lagu baru":
    st.subheader("Add a new song's lyric to your collection")
    password = st.text_input("Enter admin password to continue:", type="password")

    if password == st.secrets["admin_password"]:
        st.success("Access granted.")

        with st.form("add_song_form"):
            new_title = st.text_input("🎵 Song Title")
            new_artist = st.text_input("🎤 Artist Name")
            new_lyrics = st.text_area("📝 Paste Full Lyrics Here", height=300)
            submitted = st.form_submit_button("Add Song")

            if submitted:
                if new_title and new_artist and new_lyrics:
                    add_new_song(worksheet, new_title, new_artist, new_lyrics)
                    st.success(f"✅ '{new_title}' by {new_artist} has been added!")
                else:
                    st.error("❌ Please complete all fields.")
    elif password:
        st.error("Incorrect password.")

# --- SEARCH ONLINE ---
elif choice == "🌐 Search Lyrics Online":
    st.subheader("Search lyrics from the internet (Lyrics.ovh)")
    with st.form("search_online"):
        artist = st.text_input("Artist Name")
        title = st.text_input("Song Title")
        search = st.form_submit_button("Search")

        if search and artist and title:
            lyrics = search_lyrics_online(artist, title)
            st.text_area("Lyrics Result", value=lyrics, height=400)

            if "not found" not in lyrics.lower() and st.button("Save to Google Sheet"):
                add_new_song(worksheet, title, artist, lyrics)
                st.success(f"✅ '{title}' by {artist}' added!")

# --- MEET THE MEMBERS ---
elif choice == "👥 Meet The Members":
    st.subheader("🎸 SiBuskerz Members")
    members = load_members(members_sheet)

    for member in members:
        with st.container():
            cols = st.columns([1, 2])
            with cols[0]:
                st.image(member["Photo"], use_container_width=True)
            with cols[1]:
                st.markdown(f"### {member['Name']}")
                st.markdown(f"**Role:** {member['Role']}")
                st.markdown(f"*{member['Bio']}*")
        st.markdown("---")

# --- PERFORMANCE MODE ---
elif choice == "🎤 Performance Mode":
    st.subheader("🎤 SiBuskerz Performance Mode/Pilih Lagu-lagu untuk persembahan")

    song_data = worksheet.get_all_records()
    song_data_sorted = sorted(song_data, key=lambda x: x['Title'].lower())
    full_titles = [f"{row['Title']} - {row['Artist']}" for row in song_data_sorted]

    search_term = st.text_input("🔍 Search and filter songs (Performance Mode)")
    filtered_titles = [title for title in full_titles if search_term.lower() in title.lower()]

    selected_songs = st.multiselect("🎶 Pilih maksima 30 lagu untuk nyanyi", options=filtered_titles if search_term else full_titles, max_selections=30)

    if selected_songs:
        if st.button("🎬 Start Performance"):
            st.session_state.performance_queue = selected_songs
            st.session_state.current_song_index = 0

    # Show current song
    if "performance_queue" in st.session_state:
        queue = st.session_state.performance_queue
        index = st.session_state.get("current_song_index", 0)

        if index < len(queue):
            current_title_artist = queue[index]
            title, artist = current_title_artist.split(" - ")

            for row in song_data_sorted:
                if row["Title"] == title and row["Artist"] == artist:
                    st.markdown(f"### 🎶 Now Performing: **{title}** by *{artist}*")
                   
                    st.markdown(f"""
                    <div class="lyrics-box">
                        <pre>{row['Lyrics']}</pre>
                    </div>
                    """, unsafe_allow_html=True)

                    # st.text_area("Lyrics", value=row["Lyrics"], height=500, label_visibility="collapsed", disabled=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("⏭️ Next Song"):
                    st.session_state.current_song_index += 1
            with col2:
                if st.button("🛑 End Performance"):
                    st.session_state.pop("performance_queue", None)
                    st.session_state.pop("current_song_index", None)
                    st.success("Performance ended.")

        else:
            st.success("✅ You've finished your performance!")
            if st.button("Reset"):
                st.session_state.pop("performance_queue", None)
                st.session_state.pop("current_song_index", None)

# --- VIDEO GALLERY ---
elif choice == "🎞️ Past Performances":
    st.subheader("🎬 SiBuskerz Video Performances")

    videos = load_videos(videos_sheet)  # Your function that loads videos from the Google Sheet

    if videos:
        for i in range(0, len(videos), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(videos):
                    vid = videos[i + j]
                    with cols[j]:
                        st.markdown(f"**🎵 {vid['Title']}**")
                        st.markdown(f"*{vid['Description']}*")

                        video_link = vid['VideoLink']

                        if "drive.google.com" in video_link:
                            try:
                                # Extract the video ID from Google Drive link
                                video_id = video_link.split("/d/")[1].split("/")[0]
                                embed_url = f"https://drive.google.com/file/d/{video_id}/preview"
                                st.markdown(f"""
                                    <iframe src="{embed_url}" width="100%" height="315" allow="autoplay" allowfullscreen></iframe>
                                """, unsafe_allow_html=True)
                            except:
                                st.error("⚠️ Unable to display Google Drive video.")
                        else:
                            st.video(video_link)

                        st.markdown("---")
    else:
        st.info("No video performances listed yet.")
        
elif choice == "📍 Performance Venues & Tokens":
    
    st.subheader("🎪 Jadual Persembahan SiBuskerz & Token Penghargaan")

    # Load data
    df_perf = pd.DataFrame(performances_sheet.get_all_records())
    df_members = pd.DataFrame(members_sheet.get_all_records())

    # Display all performances
    if not df_perf.empty:
        st.markdown("### 🎤 All Performances (Upcoming & Done)")
        st.dataframe(df_perf)

        # --- PROCESS DONE PERFORMANCES ---
        done_perf = df_perf[df_perf["Status"] == "Done"].copy()

        # Clean numeric fields
        done_perf['TotalToken'] = pd.to_numeric(done_perf['TotalToken'], errors='coerce').fillna(0)
        done_perf['SharedPerPerson'] = pd.to_numeric(done_perf['SharedPerPerson'], errors='coerce').fillna(0)
        done_perf['EquipmentShare'] = pd.to_numeric(done_perf['EquipmentShare'], errors='coerce').fillna(0)

        # Count performers
        done_perf["Performers"] = done_perf["Performers"].fillna("")
        done_perf["NumPerformers"] = done_perf["Performers"].apply(
            lambda x: len([p.strip() for p in x.split(",") if p.strip()])
        )
        done_perf["TotalShares"] = done_perf["NumPerformers"] + 1

        # Recalculate share
        done_perf["SharedPerPerson"] = done_perf.apply(
            lambda row: round(row["TotalToken"] / row["TotalShares"], 2) if row["TotalShares"] > 0 else 0, axis=1
        )
        done_perf["EquipmentShare"] = done_perf["SharedPerPerson"]

        # Total calculations
        total_token = done_perf["TotalToken"].sum()
        total_distributed = (done_perf["SharedPerPerson"] * done_perf["NumPerformers"]).sum()
        total_equipment = done_perf["EquipmentShare"].sum()
        total_undistributed = total_token - (total_distributed + total_equipment)

        net_per_person = round(total_token / (done_perf["NumPerformers"].sum() + len(done_perf)), 2) if total_token > 0 else 0.0

        st.markdown(f"""
        ### 💰 Token Summary

        - 🧑‍🤝‍🧑 **Jumlah Ahli Kumpulan**: {len(df_members)}
        - 👥 **Jumlah unik artis terlibat (dari semua persembahan)**: {done_perf['NumPerformers'].sum()}
        - 🎁 **Jumlah Token penghargaan yang diterima**: RM {total_token:.2f}
        - 💸 **Jumlah bersih untuk setiap ahli**: RM {net_per_person:.2f}
        - 🎧 **Yuran Peralatan Audio (1 share)**: RM {net_per_person:.2f}
        - 🧾 **Jumlah pembahagian token kepada ahli**: RM {total_distributed:.2f}
        - 🎛️ **Jumlah Yuran Peralatan**: RM {total_equipment:.2f}
        - ❓ **Token baki belum jelas**: RM {total_undistributed:.2f}
        """)

        # --- SUMMARY PER MEMBER ---
        st.markdown("### 📊 Ringkasan Jumlah Yang Ahli Terima")
        member_earnings = {}

        for _, row in done_perf.iterrows():
            performers = [name.strip() for name in str(row["Performers"]).split(",") if name.strip()]
            share = row["SharedPerPerson"]

            for performer in performers:
                member_earnings[performer] = member_earnings.get(performer, 0) + share

        summary_df = pd.DataFrame(member_earnings.items(), columns=["Member", "TotalEarned"])
        summary_df["TotalEarned"] = summary_df["TotalEarned"].round(2)
        summary_df = summary_df.sort_values(by="TotalEarned", ascending=False)
        summary_df.index = range(1, len(summary_df) + 1)

        st.dataframe(summary_df)

        st.markdown("### 🔍 Ketahui Jumlah Token masing-masing ")
        selected_member = st.selectbox("Pilih Nama Anda", summary_df["Member"].tolist())
        personal_earning = summary_df.loc[summary_df["Member"] == selected_member, "TotalEarned"].values[0]
        st.success(f"💰 {selected_member} punya jumlah token: **RM {personal_earning:.2f}** setakat ini!")

    else:
        st.info("Tiada rekod persembahan yang dijumpai.")

    # --- ADD OR UPDATE PERFORMANCE FORM ---
    st.markdown("### ➕ Tambah atau Kemaskini Info Persembahan")

    # Check for first occurrence of "Upcoming"
    upcoming_perf = df_perf[df_perf['Status'] == 'Upcoming']
    
    if not upcoming_perf.empty:
        first_upcoming = upcoming_perf.iloc[0]
        st.info("📅 Satu persembahan akan datang dijumpai. Anda boleh kemaskini atau padamkan.")

        with st.form("update_perf_form", clear_on_submit=False):
            perf_date = st.date_input("📅 Tarikh Persembahan", pd.to_datetime(first_upcoming['Date']))
            venue = st.text_input("📍 Nama Lokasi", first_upcoming['Venue'])
            status = st.selectbox("Status", ["Upcoming", "Done"], index=1 if first_upcoming['Status'] == "Done" else 0)
            token = st.number_input("🎁 Jumlah Token Diterima (untuk 'Done' sahaja)", min_value=0.0, value=float(first_upcoming['TotalToken']) if first_upcoming['TotalToken'] else 0.0
, step=1.0) 
            notes = st.text_area("📝 Nota (pilihan)", first_upcoming.get('Notes', ''))
            member_names = df_members['Name'].tolist()
            prev_performers = [p.strip() for p in str(first_upcoming.get('Performers', '')).split(',') if p.strip()]
            attendees = st.multiselect("🎤 Siapa yang buat persembahan?", member_names, default=prev_performers)

            col1, col2 = st.columns(2)
            update_btn = col1.form_submit_button("✅ Kemaskini kepada Done or Edit")
            cancel_btn = col2.form_submit_button("❌ Batal/Padam persembahan ini")

            row_index = df_perf.index[df_perf['Date'] == first_upcoming['Date']].tolist()
            if row_index:
                sheet_row = row_index[0] + 2  # +2 to match Google Sheet row (headers + 1-based index)
            else:
                st.error("❗ Unable to locate the row in sheet.")
                st.stop()

            if cancel_btn:
                performances_sheet.delete_rows(sheet_row)
                st.success("❌ Persembahan Telah Dibatalkan dan dipadamkan.")
                st.rerun()

            if update_btn:
                if status == "Done" and not attendees:
                    st.warning("⚠️ Sila pilih artis yang terlibat sebelum penandaan sebagai Done.")
                    st.stop()

                if status == "Done":
                    num_performers = len(attendees)
                    total_shares = num_performers + 1
                    shared = round(token / total_shares, 2)
                    equipment = shared
                else:
                    shared = ""
                    equipment = ""

                performances_sheet.update(f"A{sheet_row}:H{sheet_row}", [[
                    str(perf_date),
                    venue,
                    status,
                    token if token else "",
                    shared,
                    equipment,
                    notes,
                    ", ".join(attendees)
                ]])
                st.success("✅ Persembahan telah dikemaskini.")
                st.rerun()
    else:
        st.info("🆕 Persembahan akan datang tidak dijumpai. Anda boleh tambah yang baru.")
        with st.form("add_perf_form", clear_on_submit=True):
            perf_date = st.date_input("📅 Tarikh Persembahan")
            venue = st.text_input("📍 Nama Lokasi")
            status = st.selectbox("Status", ["Upcoming", "Done"])
            token = st.number_input("🎁 Jumlah Kutipan Token  (untuk 'Done' sahaja)", min_value=0.0, value=0.0, step=1.0)
            notes = st.text_area("📝 Nota (pilihan sahaja)")
            member_names = df_members['Name'].tolist()
            attendees = st.multiselect("🎤 Siapa akan buat persembahan?", member_names)

            submitted = st.form_submit_button("➕ Tambah Persembahan")

            if submitted:
                if status == "Done" and not attendees:
                    st.warning("⚠️ Pilih sekurang-kurangnya satu artis sebelum tanda sebagai Done.")
                    st.stop()

                if status == "Done":
                    num_performers = len(attendees)
                    total_shares = num_performers + 1
                    shared = round(token / total_shares, 2)
                    equipment = shared
                else:
                    shared = ""
                    equipment = ""

                performances_sheet.append_row([
                    str(perf_date),
                    venue,
                    status,
                    token if token else "",
                    shared,
                    equipment,
                    notes,
                    ", ".join(attendees)
                ])
                st.success("✅ Persembahan baharu telah dimasukkan.")
                st.rerun()
