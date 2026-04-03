import streamlit as st
import google.genai as genai
from google.genai import types
import smtplib
import re
from email.message import EmailMessage


# --- UI Header ---
st.title("GT's Grounded Restaurant Researcher v2026")
st.write("Find local spots and get the results emailed to you.")

# --- Sidebar for Settings
with st.sidebar:
    st.header("Search Parameters")
    res_type = st.text_input("Restaurant Type", "")
    miles = st.number_input("Max Distance (miles)", min_value=1, value=5)
    address = st.text_input("From Address", "350 Macarthur Blvd, Oakland, CA")
    min_rating = st.slider("Min Google Rating", 1.0, 5.0, 4.0, format="%1.1f")
    min_reviews = st.number_input("Min Review Count", min_value=0, value=50)
    num_results = st.number_input("Number of Results", 1, 10, 5)
    recipient_email = st.text_input("Recipient Email", st.secrets["GMAIL_USER"])
    run_button = st.button("Research & Email")

# --- The Logic (Inside the button click) ---
if run_button:
    with st.spinner("Searching live web..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

            grounding_tool = types.Tool(google_search=types.GoogleSearch())

            search_query = f"Best {res_type} restaurants near {address} with at least {min_rating} stars and {min_reviews} reviews in GOOGLE MAPS"

            prompt = f"""
                        Search Query: {search_query}

                        ACT AS: A local restaurant concierge in 2026.

                        GOAL: Find {num_results} restaurants meeting these criteria:
                        - Distance: Within {miles} DRIVING miles of this specific address: {address}.
                        - Rating: Minimum {min_rating} stars in GOOGLE MAPS REVIEWS.
                        - Reviews: Minimum {min_reviews} reviews in GOOGLE MAPS REVIEWS.

                        RULES:
                        1. VERIFY: Use the search tool to ensure each spot is OPEN in 2026.
                        2. FORMATTING: Return ONLY a valid HTML table. Do NOT include markdown blocks (```html). Start immediately with <table>.
                        3. STYLING: Use <table style="width:100%; border:1px solid #333; border-collapse:collapse; font-family:sans-serif;">.
                        4. HEADER STYLING: <th style="background-color:#2c3e50; color:white; padding:8px; border:1px solid #333;">.
                        5. CELL STYLING: <td style="padding:8px; border:1px solid #ddd;">.
                        6. COLUMNS: Name, Distance, Rating, Review Count, Value Score (1-10), Value Score Rationale.
                        7. VALUE SCORE RATIONALE FORMAT: The column MUST use an HTML unordered list (<ul><li>...</li></ul>). 
                           NO plain sentences. EXACTLY 2-3 bullets per cell.
                           
                           EXAMPLE OF DESIRED RATIONALE CELL FORMAT:
                                <td>
                                    <ul>
                                        <li>High review-to-rating ratio suggests consistent quality.</li>
                                        <li>Price point is 20% lower than neighborhood average.</li>
                                        <li>Recent 2026 check-ins confirm wait times under 15 mins.</li>
                                    </ul>
                                </td>
        
                                [Begin Table Generation Now]

                        """

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[grounding_tool],
                    temperature=0.2,  # 0.2 is better for data-heavy tasks
                )
            )

            raw_text = response.text if response.text else ""

            # Strip Markdown code blocks if the AI ignored instructions
            clean_html = re.sub(r'```(?:html)?', '', raw_text).strip()

            # Extract only the content between <table> tags to avoid "Thinking" text
            table_match = re.search(r'(<table.*?>.*?</table>)', clean_html, re.DOTALL | re.IGNORECASE)

            # Get Token usage from the response object
            usage = response.usage_metadata
            in_tokens = usage.prompt_token_count
            out_tokens = usage.candidates_token_count
            # Calculate Cost (Flash-Lite 2.5: $0.10/1M in, $0.40/1M out)
            est_cost = (in_tokens * 0.0000001) + (out_tokens * 0.0000004)

            if table_match:
                research_results = table_match.group(1)
            else:
                # If no table found, use the cleaned text but ensure it's not empty
                research_results = clean_html if len(clean_html) > 10 else "No table found in AI response."

            # Display Success and Results (Existing Code)
            st.success("Research complete and email sent!")
            st.markdown(research_results, unsafe_allow_html=True)

            # Display the separate Cost Observation section at the bottom
            st.divider()
            st.subheader("Cost Observation")
            c1, c2, c3 = st.columns(3)
            c1.metric("Input Tokens", in_tokens)
            c2.metric("Output Tokens", out_tokens)
            c3.metric("Est. API Cost", f"${est_cost:.5f}")
            st.caption("Note: Does not include flat-rate Google Search grounding fees.")

            # --- Email Logic ---
            msg = EmailMessage()
            msg['Subject'] = f"Food Research: {res_type}"
            msg['From'] = st.secrets["GMAIL_USER"]
            msg['To'] = recipient_email
            # Use 'research_results' directly; it already contains the HTML
            msg.set_content("Please enable HTML to view this report.")
            msg.add_alternative(f"<html><body>{research_results}</body></html>", subtype='html')

            with smtplib.SMTP("smtp.gmail.com", port=587) as server:
                server.starttls()
                server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASS"])
                server.send_message(msg)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            # Log the full error to help debug
            st.info("Check if your API key or Gmail secrets are correct.")