import streamlit as st
import google.genai as genai
from google.genai import types
import smtplib
import re
from email.message import EmailMessage


# --- UI Header ---
st.title("Grounded Restaurant Researcher v2026")
st.write("Find local spots and get the results emailed to you.")

# --- Sidebar for Settings (Replacing the Tkinter Window) ---
with st.sidebar:
    st.header("Search Parameters")
    res_type = st.text_input("Restaurant Type", "Italian")
    miles = st.number_input("Max Distance (miles)", min_value=1, value=5)
    address = st.text_input("From Address", "City, State")
    min_rating = st.slider("Min Google Rating", 1.0, 5.0, 4.0)
    min_reviews = st.number_input("Min Review Count", min_value=0, value=50)
    num_results = st.number_input("Number of Results", 1, 15, 5)

    run_button = st.button("Research & Email")

# --- The Logic (Inside the button click) ---
if run_button:
    with st.spinner("Searching live web..."):
        try:
            # Use Streamlit Secrets for your keys (Set these up in the Streamlit Cloud dashboard)
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

            grounding_tool = types.Tool(google_search=types.GoogleSearch())

            prompt = f"""
            ACT AS: A local restaurant concierge.
            Find exactly {num_results} {res_type} restaurants within {miles} miles of {address}.
            CONSTRAINTS:
            - Min Rating: {min_rating}
            - Min Review Count: {min_reviews}
            - Research Reddit and Google for a 1-10 "Value Score" (price versus quality). Only include the result if the value score is 7/10 or better. Otherwise replace it with another result.

            FORMATTING RULES:
            1. Return ONLY the HTML. Do NOT include markdown code blocks like ```html.
            2. Use this specific inline CSS for the table: <table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd; font-family: sans-serif;">
            3. Use <th> and <td> tags with padding: 8px and border: 1px solid #ddd.
            4. COLUMNS: Name, Distance, Type, Rating, Review Count, Value Score (1-10), Summary.
            5. REVIEWS SECTION: Beneath the table, provide 1 or 2 specific illustrative reviews for each restaurant. 
            Prioritize Reddit user comments that may speak to the "Value Score".
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(tools=[grounding_tool])
            )

            # Defensive Cleaning
            research_results = response.text
            html_match = re.search(r'(<(table|html|div).*?>.*</\2>)', research_results, re.DOTALL | re.IGNORECASE)
            research_results = html_match.group(1) if html_match else research_results.strip()

            # --- Email Logic ---
            msg = EmailMessage()
            msg['Subject'] = f"Grounded Research: {res_type}"
            msg['From'] = st.secrets["GMAIL_USER"]
            msg['To'] = st.secrets["GMAIL_USER"]
            msg.add_alternative(f"<html><body>{research_results}</body></html>", subtype='html')

            with smtplib.SMTP("smtp.gmail.com", port=587) as server:
                server.starttls()
                server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASS"])
                server.send_message(msg)

            st.success("Research complete and email sent!")
            st.markdown(research_results, unsafe_allow_html=True)  # Shows results in the browser too!

        except Exception as e:
            st.error(f"Error: {e}")