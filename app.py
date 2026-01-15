import streamlit as st
import google.generativeai as genai
from PIL import Image
import tempfile
from gtts import gTTS
from io import BytesIO # <--- NOU: Pentru audio în memorie

# 1. Configurare Pagină
st.set_page_config(page_title="Doamna Învățătoare", page_icon="🧠")
st.title("🧠 Doamna Învățătoare")

# 2. Configurare API Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introdu Google API Key:", type="password")

if not api_key:
    st.stop()

genai.configure(api_key=api_key)
FIXED_MODEL_ID = "models/gemini-2.5-flash"

try:
   model = genai.GenerativeModel(
        FIXED_MODEL_ID,
        system_instruction="""Ești "Domnul Învățător" (sau Doamna Învățătoare), prietenul virtual al unui elev de clasa a 3-a (9-10 ani).

        TONUL VOCII:
        - Cald, încurajator, jucăuș, dar educativ.
        - Folosește emoji-uri (🌟, 📚, ✨, 🍎).
        - Adresează-te cu "Dragul meu", "Campionule", "Micul explorator".
        - Nu da doar răspunsul! Ghidează-l să descopere singur, ca la școală.

        REGULI PE MATERII (Clasa a III-a - Programa Românească):

        1. LIMBA ROMÂNĂ:
           - Pune mare accent pe ORTOGRAME (s-a/sa, i-a/ia, ne-am/neam). Explică-le cu trucuri (ex: "scriem 's-a' cu liniuță când putem spune 'el s-a dus'").
           - Părți de vorbire: Substantivul (ființe, lucruri), Adjectivul (însușiri - cum este?), Verbul (acțiunea - ce face?).
           - Compuneri: Încurajează creativitatea, structura (Introducere, Cuprins, Încheiere) și așezarea în pagină (alineat).

        2. MATEMATICĂ (Numere 0 - 10.000):
           - Ne concentrăm pe Tabla Înmulțirii și Împărțirii.
           - Ordinea operațiilor (întâi parantezele, apoi înmulțirea/împărțirea).
           - Probleme: Ajută-l să scoată datele problemei ("Ce știm?", "Ce se cere?").
           - Folosește exemple concrete: mere, creioane, bomboane, nu "x" și "y".

        3. ȘTIINȚE / CUNOAȘTEREA MEDIULUI:
           - Explică fenomenele (circuitul apei, plantele, corpul uman) prin povești și curiozități.

        EVALUARE:
        - Nu folosi note (1-10). Folosește CALIFICATIVE: FB (Foarte Bine), B (Bine), S (Suficient).
        - La finalul explicației, dă-i un "Super-Calificativ Virtual" și o laudă specifică (ex: "Ai câștigat un FB stelar pentru cum ai calculat!").
        """
    )
except Exception as e:
    st.error(f"Eroare model: {e}")
    st.stop()

# 3. Upload Multiplu
st.sidebar.header("📁 Materiale")
uploaded_files = st.sidebar.file_uploader("Încarcă fișiere", type=["jpg", "png", "pdf"], accept_multiple_files=True)
processed_files = []

if uploaded_files:
    for up_file in uploaded_files:
        if "image" in up_file.type:
            processed_files.append(Image.open(up_file))
            st.sidebar.image(up_file, caption=up_file.name)
        elif "pdf" in up_file.type:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(up_file.getvalue())
                path = tmp.name
            try:
                processed_files.append(genai.upload_file(path, mime_type="application/pdf"))
                st.sidebar.success(f"✅ {up_file.name}")
            except:
                st.sidebar.error("Eroare upload PDF")

# 4. Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 5. Input și Generare
if user_input := st.chat_input("Scrie ceva..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    payload = []
    for msg in st.session_state.messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        payload.append({"role": role, "parts": [msg["content"]]})
    
    current_parts = [user_input]
    if processed_files:
        current_parts.extend(processed_files)
    payload.append({"role": "user", "parts": current_parts})

    with st.chat_message("assistant"):
        with st.spinner("Scriu și pregătesc vocea..."):
            try:
                # Generare Text
                response = model.generate_content(payload)
                text = response.text
                st.write(text)
                st.session_state.messages.append({"role": "assistant", "content": text})

                # Generare Audio (Metoda Sigură cu BytesIO)
                if len(text) > 0:
                    try:
                        # Curățăm textul de simboluri care sună urât
                        clean_text = text.replace("*", "").replace("#", "").replace("$", "")
                        
                        # Creăm fișierul în memorie
                        sound_file = BytesIO()
                        tts = gTTS(text=clean_text, lang='ro')
                        tts.write_to_fp(sound_file)
                        
                        # Afișăm playerul
                        st.audio(sound_file, format='audio/mp3')
                        
                    except Exception as e_audio:
                        st.warning(f"Nu am putut genera vocea: {e_audio}")
            
            except Exception as e:
                st.error(f"Eroare: {e}")
