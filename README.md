# Bitewise

## **Real local spots. Zero guesswork.**


Bitewise is a smart, AI-powered Streamlit app that helps you discover high-quality local restaurants based on your specific cravings, location, and quality standards. It leverages **Google Gemini** with live Google Maps grounding to research actual open restaurants, then delivers a beautifully formatted HTML report straight to your email.

No more scrolling through generic lists or low-rated places — get curated, high-value recommendations with transparent scoring.

![Bitewise Header](images/neighborhood_nosh.jpg)

## ✨ Features

- **Intelligent Restaurant Research**: Uses Gemini 2.5 with Google Maps grounding to find real, currently relevant spots.
- **Strict Quality Filters**: Minimum rating, review count, distance, and openness requirements.
- **Value Scoring**: Unique 1–10 "Value Score" with clear rationale based on price, portions, quality, and real customer feedback (Google + Reddit insights).
- **Email Delivery**: Results sent as a clean, responsive HTML table to your inbox.
- **Password Protection**: Simple app-level access control.
- **Live Usage Tracking**: Shows token usage and estimated Gemini API cost for full transparency.
- **Fully Customizable**: Adjust cuisine type, max distance, minimum rating, review threshold, and number of results.

## 🚀 Live Demo

The app is deployed and running on Streamlit Cloud → **[Try Bitewise](https://restaurant-researcher-pj29vnyrj2iddzptnl8jka.streamlit.app/)**  


> **Note**: You'll need the app password (stored in secrets) to unlock the full functionality.

## 🛠️ How It Works

1. Enter your search parameters (cuisine type, address, distance, min rating, etc.).
2. The app sends a carefully crafted prompt to Gemini with Google Maps grounding.
3. Gemini returns only qualifying restaurants in a styled HTML table.
4. Results are emailed to you and displayed directly in the app.
5. You get token usage and cost breakdown for awareness.

## 📋 Requirements

- Python 3.9+
- Google Gemini API key (with Google Maps grounding enabled)
- Gmail account for sending emails (App Password recommended)
- Streamlit Cloud or any hosting platform that supports secrets

## 🔧 Installation & Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bitewise.git
   cd bitewise

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
   
3. **Set up secrets**

   Create a `.streamlit/secrets.toml` file (never commit this file):

   ```toml
   APP_PASSWORD = "your_secure_app_password"

   GEMINI_API_KEY = "your_gemini_api_key"

   GMAIL_USER = "yourgmail@gmail.com"
   GMAIL_PASS = "your_gmail_app_password"
   
4. **Run Locally**
    ```bash
   streamlit run mainstream.py

## 📁 Project Structure

bitewise/
├── app.py                  # Main Streamlit application
├── images/
│   └── neighborhood_nosh.jpg
├── .streamlit/
│   └── secrets.toml        # (not committed)
├── requirements.txt
└── README.md


## 🔐 Security Notes

- The app uses a simple password gate for access control.
- API keys and Gmail credentials are stored securely via Streamlit secrets.
- For production use, consider adding rate limiting and better authentication if sharing publicly.

## 🛣️ Roadmap / Future Improvements

- User accounts and saved searches
- Support for multiple email recipients
- Map visualization of results
- Export results to PDF
- Dark mode and improved mobile responsiveness
- Integration with additional mapping providers

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open-sourced under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for food lovers who hate settling.**

If you find Bitewise useful, please ⭐ the repo!

