import streamlit as st
import google.genai as genai
from google.genai import types
import smtplib
import re
from email.message import EmailMessage


# --- UI Header ---
st.title("GT's Grounded Restaurant Researcher v2026")
st.write("Find local spots and get the results emailed to you.")

# --- Sidebar for Settings (Replacing the Tkinter Window) ---
with st.sidebar:
    st.header("Search Parameters")
    res_type = st.text_input("Restaurant Type", "")
    miles = st.number_input("Max Distance (miles)", min_value=1, value=5)
    address = st.text_input("From Address", "City, State")
    min_rating = st.slider("Min Google Rating", 1.0, 5.0, 4.0)
    min_reviews = st.number_input("Min Review Count", min_value=0, value=50)
    num_results = st.number_input("Number of Results", 1, 10, 5)
    recipient_email = st.text_input("Recipient Email", st.secrets["GMAIL_USER"])
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
            
            STRICT FILTERING RULES:
            1. Find exactly {num_results} {res_type} restaurants within {miles} DRIVING miles of {address}.
            2. MANDATORY: You MUST discard any restaurant with a Google Rating below {min_rating}. 
            3. If a restaurant fails the {min_rating} threshold, do not mention it; find a replacement that complies.
            4. Check every result twice: [Rating >= {min_rating}] AND [Review Count >= {min_reviews}]. If both aren't True, it is an invalid result.
            
            VALUE SCORE CALCULATION:
            For each restaurant, calculate a 1-10 "Value for Price" score. 
            Before stating the score, you MUST provide a "Rationale" field that explains:
            1. The estimated average price per person based on reviews.
            2. The consensus on portion size and ingredient quality.
            3. How the cost compares to other restaurants of the same type in that specific area.

            FORMATTING RULES:
            1. Return ONLY the final HTML table and reviews. Do NOT include markdown code blocks like ```html. Do NOT include your internal reasoning or 'thought' process in the final output.
            
            2. TABLE STRUCTURE: Use <table style="border-collapse: collapse; width: 100%; border: 2px solid #2c3e50; font-family: sans-serif; color: #333333; background-color: #ffffff;">
            
            3. HEADER STYLING (CRITICAL): Every <th> tag MUST use this style: <th style="background-color: #2c3e50; color: #ffffff; padding: 12px; border: 1px solid #444; text-align: left;">
            
            4. CELL STYLING: Every <td> tag MUST use this style: <td style="padding: 10px; border: 1px solid #dddddd; color: #333333; background-color: #ffffff;">
            
            5. COLUMNS: Name, Distance, Type, Rating, Review Count, Value Score (1-10), Value Score Rationale, Summary.
            
            6. REVIEWS SECTION: Beneath the table, provide 1 or 2 specific illustrative reviews for each restaurant. 
            Format reviews using <blockquote> or a styled <div> to ensure they are distinct from the table.
            Prioritize Reddit user comments that speak to the "Value Score".
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[grounding_tool],
                )
            )

            # Defensive Cleaning
            research_results = response.text
            html_match = re.search(r'(<(table|html|div).*?>.*</\2>)', research_results, re.DOTALL | re.IGNORECASE)
            research_results = html_match.group(1) if html_match else research_results.strip()

            # --- Email Logic ---
            msg = EmailMessage()
            msg['Subject'] = f"Food Research: {res_type}"
            msg['From'] = st.secrets["GMAIL_USER"]
            msg['To'] = recipient_email
            msg.add_alternative(f"<html><body>{research_results}</body></html>", subtype='html')

            with smtplib.SMTP("smtp.gmail.com", port=587) as server:
                server.starttls()
                server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASS"])
                server.send_message(msg)

            st.success("Research complete and email sent!")
            st.markdown(research_results, unsafe_allow_html=True)  # Shows results in the browser too!

        except Exception as e:
            st.error(f"Error: {e}")