# Mood-Based Travel Itinerary Generator

An AI-powered travel planning application built with Gen AI LLM that creates personalized travel itineraries based on the user's mood, budget, country, and number of days.  

The app integrates live maps via the Nominatim library for location visualization, and can export the generated itinerary as a PDF (using ReportLab) on request.

# Features

- AI-Powered Itinerary Generation — Generates unique, mood-based travel plans using the Gemma2-9B-IT LLM.
- Gradio Frontend — Clean and interactive UI for smooth user experience.
- Live Map Integration — Displays location maps for all suggested destinations using Nominatim.
- Budget-Friendly Suggestions — Adapts recommendations to your given budget.
- Custom Trip Duration — Plans are tailored to your preferred number of travel days.
- PDF Export — Download the itinerary as a PDF using ReportLab.

# Tech Stack

- LLM Model: Gemma2-9B-IT (https://ai.google.dev/gemma)
- Frontend: Gradio (https://www.gradio.app/)
- Mapping API: Nominatim (https://nominatim.org/)
- Backend: Python
- PDF Generation: ReportLab (https://www.reportlab.com/)


# Project Structure
├── app.py             # Main application script
├── requirements.txt   # Python dependencies
├── images/            # Mood-related image assets
└── README.md          # Project documentation
