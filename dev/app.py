import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# --- Configuration ---
app = Flask(__name__)
# Construct the path to the 'uploads' folder relative to the project root
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# --- Data Storage ---
race_data = None
current_lap = 0

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

# --- Core Logic ---
def process_lap_data(lap_number):
    """Processes data for a given lap and returns strategic insights."""
    if race_data is None or lap_number >= len(race_data):
        return None

    lap_time = race_data['lap_time'].iloc[lap_number]

    # Insights (placeholders)
    pit_window_recommendation = "Stay out"
    next_lap_pace_prediction = lap_time * 1.01  # Simple prediction
    performance_anomaly = "No"

    # Pit window logic (simple decay)
    if lap_number > 5:
        recent_laps = race_data['lap_time'].iloc[lap_number-3:lap_number]
        if lap_time > recent_laps.mean() * 1.02:
            pit_window_recommendation = "Pit now"
        elif lap_time > recent_laps.mean() * 1.01:
            pit_window_recommendation = "Pit soon"

    # Anomaly detection
    if lap_number > 1:
        if lap_time > race_data['lap_time'].iloc[lap_number-1] * 1.05:
            performance_anomaly = "Yes"

    return {
        "lap_number": lap_number + 1,
        "lap_time": lap_time,
        "pit_recommendation": pit_window_recommendation,
        "next_lap_prediction": f"{next_lap_pace_prediction:.3f}",
        "anomaly": performance_anomaly,
        "lap_times": race_data['lap_time'].iloc[:lap_number+1].tolist()
    }

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global race_data, current_lap
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        create_upload_folder()
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Use python engine and sep=None to auto-detect separator
            race_data = pd.read_csv(filepath, sep=None, engine='python')
        except Exception:
            # Fallback for very tricky files
            race_data = pd.read_csv(filepath, sep=None, engine='python', encoding='latin1')
        current_lap = 0
        
        return "File uploaded successfully", 200
    return "File upload failed", 500

@app.route('/data')
def get_data():
    global current_lap
    data = process_lap_data(current_lap)
    if data:
        current_lap += 1
        return jsonify(data)
    return jsonify({"status": "end_of_race"})

@app.route('/reset', methods=['POST'])
def reset_race():
    """Resets the current lap to the beginning."""
    global current_lap
    current_lap = 0
    return "Race reset successfully", 200

if __name__ == '__main__':
    app.run(debug=True, port=5004)
