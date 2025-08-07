import spacy.cli
spacy.cli.download("en_core_web_sm")
import os
import gradio as gr
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import spacy
from geopy.geocoders import Nominatim
import folium

# Load API key securely from environment
GR_API_KEY = os.getenv("GR_API_KEY")
client = Groq(api_key=GR_API_KEY)

MOODS = [
    "Adventure",
    "Relaxing",
    "Romantic",
    "Cultural & Heritage",
    "Foodie & Culinary",
    "Shopping & Urban",
    "Beach & Island",
    "Any"
]

MOOD_IMAGES = {
    "Adventure": "images/adventure.png",
    "Relaxing": "images/relaxing.png",
    "Romantic": "images/romantic.png",
    "Cultural & Heritage": "images/cultural.png",
    "Foodie & Culinary": "images/foodie.png",
    "Shopping & Urban": "images/shopping.png",
    "Beach & Island": "images/beach.png",
    "Any": "images/default.png"
}

# Load SpaCy model once globally
nlp = spacy.load("en_core_web_sm")

def clean_place_name(name):
    import re
    return re.sub(r'^(the|a|an)\s+', '', name, flags=re.IGNORECASE).strip()

def extract_places_and_map(itinerary_text, city_context=None):
    # Extract places using regex + NER
    pattern = r"(visit|explore|trip to|at|go to|see)\s+([A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)"
    matches = re.findall(pattern, itinerary_text, re.IGNORECASE)
    rule_places = [m[1].strip() for m in matches]

    doc = nlp(itinerary_text)
    ner_places = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"]]

    places = list(set(rule_places + ner_places))

    geolocator = Nominatim(user_agent="feelaway_app")
    locations = []
    for place in places:
        try:
            query = f"{place}, {city_context}" if city_context else place
            loc = geolocator.geocode(query, language='en', timeout=10)
            if loc:
                locations.append((place, loc.latitude, loc.longitude))
        except Exception:
            continue

    if not locations:
        return "<p>No locations found for mapping.</p>"

    # Create Folium map
    m = folium.Map(location=[locations[0][1], locations[0][2]], zoom_start=10)
    for name, lat, lon in locations:
        folium.Marker([lat, lon], popup=name).add_to(m)

    # Return full HTML (with JS & CSS)
    return m._repr_html_()

def generate_itinerary(mood, location, budget, days):
    mood_text = "any mood" if mood == "Any" else mood
    budget_text = "any budget" if budget == "Any" else budget
    location_text = location if location.strip() != "" else "any destination"
    
    prompt = (
        f"Create a {days}-day travel itinerary to {location_text}. "
        f"The mood of the traveler is {mood_text} and the budget is {budget_text}. "
        f"Use Markdown formatting with **bold headings** for days and time slots."
    )
    
    completion = client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[
            {"role": "system", "content": "You are an expert travel planner."},
            {"role": "user", "content": prompt}
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False
    )
    
    itinerary_text = completion.choices[0].message.content
    image_path = os.path.abspath(MOOD_IMAGES.get(mood, MOOD_IMAGES["Any"]))

    # Generate map HTML from itinerary text and user location
    map_html = extract_places_and_map(itinerary_text, city_context=location_text if location_text.lower() != "any destination" else None)

    return itinerary_text, image_path, map_html

def generate_pdf(itinerary_text):
    if not itinerary_text.strip():
        return None,gr.update(visible=False)

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "feelaway_itinerary.pdf")

    if os.path.exists(temp_path):
        os.remove(temp_path)

    doc = SimpleDocTemplate(temp_path, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "Times-Roman"
    style.fontSize = 14
    style.leading = 18

    html_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', itinerary_text)
    paragraphs = html_text.split('\n')

    story = []
    for para in paragraphs:
        p = Paragraph(para if para.strip() else ' ', style)
        story.append(p)
        story.append(Spacer(1, 6))

    doc.build(story)

    return temp_path,gr.update(visible=True)


with gr.Blocks(theme=gr.themes.Default(primary_hue="teal", secondary_hue="teal")) as demo:
    header_html = """
    <style>
    @keyframes colorCycle {
        0% { color: #008080; }
        25% { color: #20b2aa; }
        50% { color: #40e0d0; }
        75% { color: #008080; }
        100% { color: #20b2aa; }
    }
    .color-cycle { animation: colorCycle 3s infinite; }
    .tagline { font-style: italic; color: #007777; font-size: 18px; margin-top: 4px; }
    #map-container iframe {
    width: 100% !important;
    height: 500px !important;
    border-radius: 8px;
    overflow:hidden;
    }
    #image-container img {
        width: 100% !important;
        height: 500px !important;
        object-fit: cover;
        border-radius: 8px;
    }
    .equal-row {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        justify-items: center;
    }
    </style>
    <div style='text-align: center;'>
        <h1 class="color-cycle" style="font-size: 38px; margin-bottom: 0;">FEEL AWAY APP</h1>
        <p class="tagline">"Your Mood, Your Journey – Personalized Itineraries, Instantly"</p>
    </div>
    """
    with gr.Row():
        gr.HTML(header_html)

    with gr.Row():
        mood = gr.Dropdown(MOODS, label="Mood", value="Any", info="Select the mood of your trip")
        location = gr.Textbox(label="Destination", placeholder="e.g., India, Japan, France (leave blank for Any)", info="Where do you want to go?")
    
    with gr.Row():
        budget = gr.Dropdown(["Low", "Medium", "High", "Any"], label="Budget", value="Any", info="Choose your budget level")
        days = gr.Slider(1, 10, value=5, step=1, label="Days", info="Number of days for the itinerary")
    
    generate_btn = gr.Button("✨ Generate Itinerary", variant="primary")

    with gr.Column():
        itinerary_output = gr.Markdown(label="Generated Itinerary")
        
        with gr.Row(elem_classes="equal-row"):
            with gr.Column(scale=1):
                image_output = gr.Image(label="Travel Mood Image",type="filepath")
            with gr.Column(scale=1):
                map_output = gr.HTML(label="Map of Suggested Places",elem_id="map-container")

    with gr.Column():
        download_btn = gr.Button("Download Itinerary as PDF",variant="secondary")
        pdf_file = gr.File(label="Download PDF", file_types=[".pdf"],visible=False)

    generate_btn.click(
        generate_itinerary,
        inputs=[mood, location, budget, days],
        outputs=[itinerary_output, image_output, map_output],
        show_progress=True
    )
    download_btn.click(
        generate_pdf,
        inputs=[itinerary_output],
        outputs=[pdf_file, pdf_file]
    )

demo.launch()
