import streamlit as st
import speech_recognition as sr
import pyttsx3
import threading
import pandas as pd
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile

# Initialize session state attributes if not already set
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []
if "interaction_log" not in st.session_state:
    st.session_state.interaction_log = pd.DataFrame(columns=["user_query", "assistant_response"])

# Ensure language_preference and user_logged_in are initialized
if "language_preference" not in st.session_state:
    st.session_state.language_preference = "English"
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

# Function to convert text to speech using threading
engine = pyttsx3.init()
engine_lock = threading.Lock()
stop_flag = False  # Global flag to stop the speech

def speak(text):
    """Function to speak the given text."""
    global stop_flag
    stop_flag = False  # Reset stop flag when new speech starts

    def _speak():
        global stop_flag
        with engine_lock:  # Ensure only one speech instance runs at a time
            engine.say(text)
            engine.runAndWait()

    speak_thread = threading.Thread(target=_speak)
    speak_thread.start()

def stop_speech():
    """Function to stop speech synthesis."""
    global stop_flag
    stop_flag = True
    with engine_lock:
        engine.stop()  # Stop pyttsx3 engine

def listen_for_stop():
    """Listens for the user to say 'stop' and stops speech if detected."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say 'Stop' to interrupt speech...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)  # Waits for user input
            command = recognizer.recognize_google(audio).lower()
            if "stop" in command:
                print("Stopping speech...")
                stop_speech()
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError:
            print("Error connecting to recognition service.")
        except sr.WaitTimeoutError:
            print("No input detected.")


# Function for voice input (speech to text)
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            st.write(f"Voice Input: {query}")
            return query
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand that.")
        except sr.RequestError:
            st.error("Sorry, the speech service is down.")

# Load patterns from JSON file
def load_patterns():
    try:
        with open('legal_patterns.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": "Patterns file not found."}
    except json.JSONDecodeError:
        return {"error": "Error decoding the patterns file."}

patterns = load_patterns()

# Define response function based on patterns
def get_response(query):
    query = query.lower().strip()
    if len(query) < 3:
        return translations[st.session_state.language_preference]["no_response"]

    # Add the latest user query to the conversation context
    st.session_state.conversation_context.append(f"User: {query}")

    # Check for matching patterns
    for item in patterns:
        pattern = item['pattern'].lower().strip()
        if pattern in query:
            response = item['response']
            st.session_state.conversation_context.append(f"Assistant: {response}")
            return response

    return translations[st.session_state.language_preference]["no_response"]

# Language Translation Dictionary
translations = {
    "English": {
    "ask_query": "Ask your query for legal assistance",
    "thinking": "Thinking ✨...",
    "no_response": "Sorry, I couldn't find a matching response for your query.",
    "positive_feedback": "👍 Positive feedback",
    "negative_feedback": "👎 Negative feedback",
    "login_button": "Login",
    "welcome": "Welcome",
    "faq_button": "Show FAQs",
    "download_button": "Download",
    "interaction_history": "Show Interaction History",
    "voice_query": "Voice Query 🎙️",
    "view_history": "View History 📜",
    "download_law": "Download Law 📁",
    "info_section": "**Legal Laws Advisor Bot:📄**\n- **Objective:** Developed a conversational chatbot to provide legal law info and assistance.\n- **Features**:📜\n  - Allows users to ask their query of law.\n  - Provides a response to user query. ✔\n  - Offers a user-friendly interface for asking legal questions."
},
    "Hindi - हिन्दी": {
        "ask_query": "कानूनी सहायता के लिए अपना प्रश्न पूछें",
        "thinking": "सोच रहे हैं ✨...",
        "no_response": "मुझे आपके प्रश्न का मिलान करने वाला उत्तर नहीं मिला।",
        "positive_feedback": "👍 सकारात्मक प्रतिक्रिया",
        "negative_feedback": "👎 नकारात्मक प्रतिक्रिया",
        "login_button": "लॉगिन करें",
        "welcome": "स्वागत है",
        "faq_button": "सामान्य प्रश्न दिखाएँ",
        "download_button": "चैट इतिहास डाउनलोड करें",
        "interaction_history": "इंटरएक्शन इतिहास दिखाएँ",
        "voice_query": "आवाज़ से पूछें 🎙️",
        "view_history": "इतिहास देखें 📜",
        "download_law": "कानून डाउनलोड करें 📁",
         "info_section": """
        **कानूनी क़ानून सलाहकार बॉट📄**
        - **लक्ष्य:** कानूनी क़ानून जानकारी और सहायता प्रदान करने के लिए एक संवादात्मक चैटबॉट विकसित किया गया।
        - **विशेषताएँ:**📜
          -  उपयोगकर्ताओं को कानून से संबंधित प्रश्न पूछने की अनुमति देता है। 𓍝
          -  उपयोगकर्ता के प्रश्न का उत्तर प्रदान करता है। ✔
          -  उपयोगकर्ता के प्रश्न का विस्तृत विवरण, दंड, लाभ, और हानियाँ प्रदर्शित करता है। ✉︎
          -  कानूनी प्रश्न पूछने के लिए एक उपयोगकर्ता-मित्र इंटरफेस प्रदान करता है। 🔗
        """
    },
    "Telugu - తెలుగు": {
        "ask_query": "న్యాయ సహాయం కోసం మీ ప్రశ్నను అడగండి",
        "thinking": "ఆలోచిస్తున్నాను ✨...",
        "no_response": "మీ ప్రశ్నకు సరిపడే సమాధానం కనుగొనలేకపోయాను.",
        "positive_feedback": "👍 సానుకూల అభిప్రాయం",
        "negative_feedback": "👎 ప్రతికూల అభిప్రాయం",
        "login_button": "లాగిన్ చేయండి",
        "welcome": "స్వాగతం",
        "faq_button": "ఎఫ్ ఏ క్యూ లను చూపించండి",
        "download_button": "చాట్ చరిత్రను డౌన్‌లోడ్ చేయండి",
        "interaction_history": "మాట్లాడిన చరిత్ర చూపించు",
        "voice_query": "వాయిస్ క్వెరీ 🎙️",
        "view_history": "చరిత్ర చూడండి 📜",
        "download_law": "డౌన్‌లోడ్ చేయండి 📁",
        "info_section": """
        **చట్టాల సలహా బాట్📄**
        - **ఉద్దేశం:** చట్టాల సమాచారం మరియు సహాయం అందించడానికి ఒక సంభాషణ చాట్‌బాట్‌ను అభివృద్ధి చేయడం।
        - **ప్రతి పౌరుడు చట్టాల గురించి అవగాహన కలిగి ఉండాలి.
        - **సదుపాయాలు:**📜
          -  వినియోగదారులు చట్టం గురించి తమ ప్రశ్నను అడగగలుగుతారు। 𓍝
          -  వినియోగదారుల ప్రశ్నకు సమాధానం అందిస్తుంది। ✔
          -  వినియోగదారు ప్రశ్నకు సంబంధించిన వివరణ, శిక్షలు, లాభాలు మరియు నష్టాలను ప్రదర్శిస్తుంది। ✉︎
          -  చట్టంపై ప్రశ్నలను అడగడానికి వినియోగదారు-అనుకూల ఇంటర్‌ఫేస్ అందిస్తుంది। 🔗
        - **ప్రాముఖ్యత:** సంభాషణ కృత్రిమ నుణ్ణి గుణం ద్వారా చట్ట సమాచారాన్ని అందించే లోనిపడి సరళత, సామర్థ్యం మరియు యాక్సెస్‌పై దృష్టి సారిస్తుంది। 📝
        """
    },
    "Tamil - தமிழ்": {
        "ask_query":"சட்ட உதவிக்கு உங்கள் கேள்வியைக் கேளுங்கள்",
        "thinking": "சிந்தித்து கொண்டிருக்கிறேன் ✨...",
        "no_response": "உங்கள் கேள்விக்கான பதிலை காணவில்லை.",
        "positive_feedback": "👍 நல்ல கருத்து",
        "negative_feedback": "👎 எதிர்மறை கருத்து",
        "login_button": "உள்நுழைய",
        "welcome": "வரவேற்கிறேன்",
        "faq_button": "கேள்விகளை காண்பிக்கவும்",
        "download_button": "அரட்டை வரலாற்றைப் பதிவிறக்கவும்",
        "interaction_history": "உரையாடல் வரலாற்றைக் காண்பிக்கவும்",
        "voice_query": "குரல் கேள்வி 🎙️",
        "view_history": "வரலாற்றைக் காண்க 📜",
        "download_law": "சட்டத்தை பதிவிறக்கவும் 📁",
        "info_section": """
        **சட்ட ஆலோசகர்போட்📄**
        - **நோக்கம்:** சட்ட தகவல்கள் மற்றும் உதவியை வழங்குவதற்காக உருவாக்கப்பட்ட ஒரு உரையாடல் சாட் பாட்டை உருவாக்கியது.
        - **ஒவ்வொரு குடிமகனும் சட்டங்களைப் பற்றி அறிந்திருக்க வேண்டும்.**
        - **சாதனைகள்:**📜
          -  பயனாளர்களுக்கு சட்டம் பற்றிய கேள்விகளை கேட்க அனுமதிக்கின்றது। 𓍝
          -  பயனாளரின் கேள்விக்கு பதில் அளிக்கின்றது। ✔
          -  பயனாளரின் கேள்விக்கு தொடர்புடைய விளக்கம், தண்டனைகள், நன்மைகள் மற்றும் தீமைகளை காட்டுகின்றது। ✉︎
          -  சட்டங்களைப் பற்றி கேட்க பயனாளர் நட்பான இடைமுகத்தை வழங்குகிறது। 🔗
        - **முக்கியத்துவம்:** உரையாடல் செயற்கை நுண்ணறிவு வழியாக சட்ட தகவல்களை வழங்குவதில் எளிமை, திறன் மற்றும் அணுகுமுறை என்பதிலுள்ள கவனம். 📝
        """
    },
    "Kannada - ಕನ್ನಡ": {
    "ask_query": "ನಿಮ್ಮ ಕಾನೂನು ಸಹಾಯಕ್ಕಾಗಿ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ",
    "thinking": "ಆಲೋಚನೆ ✨...",
    "no_response": "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಹೊಂದುವ ಉತ್ತರವನ್ನು ನಾನು ಕಂಡುಹಿಡಿಯಲಿಲ್ಲ.",
    "positive_feedback": "👍 ಉತ್ತಮ ಪ್ರತಿಕ್ರಿಯೆ",
    "negative_feedback": "👎 ಹೀನಾಯ ಪ್ರತಿಕ್ರಿಯೆ",
    "login_button": "ಲಾಗಿನ್",
    "welcome": "ಸ್ವಾಗತ",
    "faq_button": "FAQಗಳನ್ನು ತೋರಿಸಿ",
    "download_button": "ಚಾಟ್ ಇತಿಹಾಸವನ್ನು PDFಗೆ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    "interaction_history": "ಇಂಟರಾಕ್ಷನ್ ಇತಿಹಾಸವನ್ನು ತೋರಿಸಿ",
    "voice_query": "ಧ್ವನಿ ಪ್ರಶ್ನೆ 🎙️",
    "view_history": "ಇತಿಹಾಸ ವೀಕ್ಷಿಸಿ 📜",
    "download_law": "ಕಾನೂನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ 📁",
    "info_section": "**ಕಾನೂನು ಸಲಹೆಗಾರ ಬಾಟ್:📄**\n- **ಉದ್ದೇಶ:** ಕಾನೂನು ಮಾಹಿತಿ ಮತ್ತು ಸಹಾಯ ನೀಡಲು ಸಂವಾದಾತ್ಮಕ ಚಾಟ್‌ಬಾಟ್ ಅನ್ನು ಅಭಿವೃದ್ಧಿಪಡಿಸಲಾಗಿದೆ.\n- **ವೈಶಿಷ್ಟ್ಯಗಳು:**📜\n  - ಬಳಕೆದಾರರಿಗೆ ಕಾನೂನು ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಲು ಅವಕಾಶ ನೀಡುತ್ತದೆ.\n  - ಬಳಕೆದಾರರ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರವನ್ನು ನೀಡುತ್ತದೆ. ✔\n  - ಕಾನೂನು ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಲು ಬಳಕೆದಾರ-ಹಿತಕರ ಇಂಟರ್‌ಫೇಸ್ ಅನ್ನು ಒದಗಿಸುತ್ತದೆ."
},
    "Malayalam - മലയാളം": {
    "ask_query": "നിങ്ങളുടെ നിയമ സഹായത്തിനായുള്ള ചോദ്യം ചോദിക്കുക",
    "thinking": "ചിന്തിക്കുന്നു ✨...",
    "no_response": "ക്ഷമിക്കണം, നിങ്ങളുടെ ചോദ്യത്തിന് അനുയോജമായ പ്രതികരണം കണ്ടെത്താനായില്ല.",
    "positive_feedback": "👍 സാന്ദര്യപരമായ പ്രതികരണം",
    "negative_feedback": "👎 പ്രതികൂല പ്രതികരണം",
    "login_button": "ലോഗിൻ",
    "welcome": "സ്വാഗതം",
    "faq_button": "FAQ കാണിക്കുക",
    "download_button": "ചാറ്റ് ചരിത്രം PDF ആയി ഡൗൺലോഡ് ചെയ്യുക",
    "interaction_history": "ഇന്ററാക്ഷൻ ചരിത്രം കാണിക്കുക",
    "voice_query": "ശബ്ദ ചോദ്യം 🎙️",
    "view_history": "ചരിത്രം കാണുക 📜",
    "download_law": "നിയമം ഡൗൺലോഡ് ചെയ്യുക 📁",
    "info_section": "**നിയമ ഉപദേഷ്ടാവ് ബോട്ട്:📄**\n- **ലക്ഷ്യം:** നിയമ വിവരങ്ങളും സഹായവും നൽകാൻ സംഭാഷണ ചാറ്റ്‌ബോട്ട് വികസിപ്പിച്ചിരിക്കുന്നു.\n- **സവിശേഷതകൾ:**📜\n  - ഉപയോക്താക്കളെ നിയമ ചോദ്യങ്ങൾ ചോദിക്കാൻ അനുവദിക്കുന്നു.\n  - ഉപയോക്തൃ ചോദ്യത്തിന് പ്രതികരണം നൽകുന്നു. ✔\n  - നിയമ ചോദ്യങ്ങൾ ചോദിക്കാൻ ഉപയോക്തൃ സൗഹൃദ ഇന്റർഫേസ് നൽകുന്നു."
}
}
# Streamlit Title
st.title("LEGAL LAW  ADVISOR BOT 🎗️")

# Load and display the info section
st.info(translations[st.session_state.language_preference]["info_section"])

# Language selection from the sidebar
language_preference = st.sidebar.selectbox(
    "Welcome Select your preferred language :",
    ["English", "Hindi - हिन्दी", "Telugu - తెలుగు", "Tamil - தமிழ்", "Malayalam - മലയാളം", "Kannada - ಕನ್ನಡ"],
    index=["English", "Hindi - हिन्दी", "Telugu - తెలుగు", "Tamil - தமிழ்", "Malayalam - മലയാളം", "Kannada - ಕನ್ನಡ"].index(st.session_state.language_preference)
)

# Save selected language preference in session state
if language_preference != st.session_state.language_preference:
    st.session_state.language_preference = language_preference

# User login logic
if not st.session_state.user_logged_in:
    # Prompt for the user's name
    st.session_state.username = st.text_input("Enter your name to start chatting with legal laws assistant 🎗️")
    if st.session_state.username:
        st.session_state.user_logged_in = True
        st.rerun()
else:
    # Once logged in, show the legal assistant functionalities
    st.write(f"👋 Hello {st.session_state.username}! {translations[st.session_state.language_preference]['ask_query']}")
    prompt = st.chat_input(translations[st.session_state.language_preference]["ask_query"])

    if prompt:
        st.write(f"👤 Your Query: {prompt}")
        response = get_response(prompt)
        st.write(f"🤖 Response: {response}")

        new_log = {"user_query": prompt, "assistant_response": response}
        st.session_state.interaction_log = pd.concat(
            [st.session_state.interaction_log, pd.DataFrame([new_log])], ignore_index=True
        )
    
    
    # Adding custom styling for buttons
    st.markdown("""
        <style>
            body {
                color: black;
            }
            .stButton>button {
                border: 2px solid #2c6e49;
                border-radius: 8px;
                color: white;
                padding: 5px 7px;
                font-size: 6px;
                margin: 10px;
                cursor: pointer;
            }
            .stButton>button:hover {
                background-color: #a50104;
                border: 2px solid #a50104;
                color: white;
            }
            p.pp {
                color: white !important;
            }
            .st-al {
                color: rgb(0 0 0);
            }
            .st-au {
                background-color:#427aa1 ;
            }
            .st-emotion-cache-1a9obov {
                color: rgb(0 0 0) !important;
            }
            .st-emotion-cache-1qg05tj {
                color: rgb(0 0 0) !important;
            }
            .st-emotion-cache-opmzsf {
                position: absolute;
                background: rgb(141, 153, 174);
                color: rgb(0 0 0);
                inset: 0px;
                color-scheme: dark;
                overflow: hidden;
            }
        </style>
    """, unsafe_allow_html=True) 

    col1, col2, col3 = st.columns(3)

    # Speech to Text Button
    with col1:
        if st.button(translations[st.session_state.language_preference]["voice_query"]):
            query = listen()
            if query:
                st.session_state.messages.append(query)
                st.write(f"Your Query: {query}")
                response = get_response(query)
                st.write(f"Assistant Response: {response}")
                speak(response)  # Speak the response

                # Save voice query and response in interaction history
                new_log = {"user_query": query, "assistant_response": response}
                st.session_state.interaction_log = pd.concat(
                    [st.session_state.interaction_log, pd.DataFrame([new_log])], ignore_index=True
                )
    # Interaction History Button
    with col2:
        if st.button(translations[st.session_state.language_preference]["view_history"]):
            st.dataframe(st.session_state.interaction_log)

    def generate_pdf():
        """Creates a PDF file from interaction history and returns the file path."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.setFont("Helvetica", 12)
            
            c.drawString(100, 750, "Legal Laws Assistant - Chat History")
            y_position = 720

            # Loop through interaction history
            for index, row in st.session_state.interaction_log.iterrows():
                user_query = row["user_query"]
                assistant_response = row["assistant_response"]
                
                # Write the user's query
                c.drawString(80, y_position, f"👤 User: {user_query}")
                y_position -= 20  # Move cursor down

                # Write the assistant's response
                c.drawString(100, y_position, f"🤖 Assistant: {assistant_response}")
                y_position -= 30  # Space between entries

                # Check if the page needs to be added
                if y_position < 50:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y_position = 750

            c.save()
            return pdf_path

    # Download Button for PDF
    with col3:
        if st.button(translations[st.session_state.language_preference]["download_button"]):
            pdf_path = generate_pdf()
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📄 Download Chat as PDF",
                    data=f,
                    file_name="Chat_History.pdf",
                    mime="application/pdf",
                )


# Folder where templates are stored
TEMPLATES_FOLDER = "template"

# Legal templates with file names
legal_templates = {
    "Rental Agreement": "rental_agreement_template.pdf",
    "Loan Agreement":"loan-agreement-template.pdf",
    "Employment Agreement": "employment_agreement_template.pdf",
    "Business Agreement": "partnership_agreement_template.pdf",
    "Freelancer Agreement": "freelancer_contract_template.pdf",
    "Invoice Agreement": "invoice_template.pdf",
    "Lease Agreement": "lease_agreement_template.pdf",
    "Service Agreement": "service_agreement_template.pdf",
    "Non-Disclosure Agreement": "nda_template.pdf"  
}

# Sidebar for Language Selection (now for templates)
with st.sidebar:
    # Language selection dropdown for templates with placeholder
    template_selection = st.selectbox(
        "Select a legal template to download :",  # Title for the dropdown
        ["Select a template"] + list(legal_templates.keys())  # Add a placeholder option
    )

# Get the selected template's file name
if template_selection != "Select a template":  # Ensure a valid selection is made
    selected_template_file = legal_templates.get(template_selection)

    # Check if the selected template file exists and provide the download button
    if selected_template_file:
        file_path = os.path.join(TEMPLATES_FOLDER, selected_template_file)
        
        if os.path.exists(file_path):  # Check if the file exists
            with open(file_path, "rb") as file:
                st.sidebar.download_button(
                    label=f"📄 Download {template_selection}",
                    data=file,
                    file_name=selected_template_file,
                    mime="application/pdf"
                )
        else:
            st.sidebar.warning(f"Template '{template_selection}' is not available.")

if __name__ == '__main__':
    response = "Hello, welcome to Legal Law Advisor Bot! Say 'stop' to interrupt audio Output."
    
    # Start both speech and listening for "stop" in separate threads
    speak(response)
    stop_thread = threading.Thread(target=listen_for_stop)
    stop_thread.start()