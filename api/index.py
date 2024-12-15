from flask import Flask, request, jsonify, render_template, send_from_directory, Response
import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import json
import traceback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates')),
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
)

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

def process_image(image_data):
    """Process image data and return base64 encoded parts."""
    try:
        return [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_data).decode('utf-8')
        }]
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

def process_gemini_response(response_text):
    """Process and validate Gemini response."""
    try:
        # Clean up the response text
        cleaned_text = response_text.strip()
        if not cleaned_text.startswith('{'):
            start_idx = cleaned_text.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in response")
            cleaned_text = cleaned_text[start_idx:]
        
        if not cleaned_text.endswith('}'):
            end_idx = cleaned_text.rfind('}')
            if end_idx == -1:
                raise ValueError("No JSON object found in response")
            cleaned_text = cleaned_text[:end_idx + 1]
        
        # Parse JSON
        data = json.loads(cleaned_text)
        
        # Validate structure
        required_keys = {'company_details', 'invoice_details', 'line_items', 'totals'}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        # Convert numeric values
        for item in data['line_items']:
            item['quantity'] = float(str(item['quantity']).replace(',', ''))
            item['price'] = float(str(item['price']).replace(',', ''))
            item['total'] = float(str(item['total']).replace(',', ''))
        
        data['totals']['subtotal'] = float(str(data['totals']['subtotal']).replace(',', ''))
        data['totals']['tax'] = float(str(data['totals']['tax']).replace(',', ''))
        data['totals']['total'] = float(str(data['totals']['total']).replace(',', ''))
        
        return data
    
    except Exception as e:
        logger.error(f"Error processing Gemini response: {str(e)}")
        logger.error(f"Raw response: {response_text}")
        raise

@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Check for file
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']
        if not file:
            return jsonify({
                'status': 'error',
                'error': 'Empty file'
            }), 400

        # Process image
        image_data = file.read()
        image_parts = process_image(image_data)

        # Generate content using Gemini
        prompt = """Analyze this Hebrew invoice image and return ONLY a JSON object with this exact structure:
{
    "company_details": {
        "name": "כרמל מעדנים בע״מ",
        "address": "סעדיה גאון 19, תל-אביב",
        "tax_id": "513203414"
    },
    "invoice_details": {
        "invoice_number": "",
        "date": ""
    },
    "line_items": [
        {
            "item_code": "",
            "description": "",
            "quantity": 0,
            "price": 0,
            "total": 0
        }
    ],
    "totals": {
        "subtotal": 0,
        "tax": 0,
        "total": 0
    }
}

IMPORTANT: Return ONLY the JSON object, no other text."""

        # Log request to Gemini
        logger.info("Sending request to Gemini")
        response = model.generate_content([prompt, image_parts[0]])
        logger.info("Received response from Gemini")

        # Log raw response
        response_text = response.text
        logger.info(f"Raw response: {response_text}")

        # Process response
        invoice_data = process_gemini_response(response_text)

        # Return success response
        return jsonify({
            'status': 'success',
            'invoice_data': invoice_data
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=False)