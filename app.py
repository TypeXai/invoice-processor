"""
Invoice Processing Application with Gemini Vision AI
Vercel Serverless Compatible Version
"""

import os
import base64
import json
import logging
import re
from typing import Dict, List, Union, Optional
from flask import Flask, request, jsonify, render_template, make_response
import google.generativeai as genai
from dotenv import load_dotenv
import traceback
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import asyncio
from functools import partial
import time
import requests
from flask_cors import CORS

# Configuration and Setup
# ----------------------

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with serverless settings
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024  # 6MB max for Vercel

# Initialize CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5000",
            "https://invoice-processor-app.web.app",
            "https://invoice-processor-app.firebaseapp.com",
            "https://gemini-invoice-processor.onrender.com"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

# Gemini AI Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
model = None

def initialize_gemini():
    """Initialize Gemini model if API key is available."""
    global model
    if GOOGLE_API_KEY:
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            logger.info("Initialized Gemini model: gemini-1.5-pro-latest")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            model = None
    else:
        logger.warning("GOOGLE_API_KEY not set - Gemini features will be disabled")

# Initialize Gemini if possible
initialize_gemini()

# Upload Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit for Vercel

# Type Definitions and Utility Functions
# --------------------------------

InvoiceData = Dict[str, Union[Dict, List]]
JsonResponse = tuple[Dict[str, Union[str, Dict]], int]

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image_memory(file_data: bytes) -> List[Dict[str, str]]:
    """Process image data in memory with optimized size."""
    try:
        # Always compress image for consistent processing time
        from PIL import Image
        import io
        
        # Open image from bytes
        img = Image.open(io.BytesIO(file_data))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate new size while maintaining aspect ratio
        max_size = (600, 600)  # Reduced size for faster processing
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Optimize image
        output = io.BytesIO()
        img.save(output, 
                format='JPEG', 
                quality=70,      # Reduced quality for smaller size
                optimize=True,
                progressive=True # Progressive loading
        )
        file_data = output.getvalue()
        
        # Log image size
        logger.info(f"Processed image size: {len(file_data) / 1024:.2f}KB")
        
        return [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(file_data).decode('utf-8')
        }]
    except Exception as e:
        logger.error(f"Error processing image in memory: {str(e)}")
        raise

# Gemini Vision AI Prompt
# ----------------------

GEMINI_PROMPT = """Analyze this Hebrew invoice image and extract the data into a JSON object with PRECISE field mapping.

CRITICAL RTL COLUMN ORDER AND MAPPING RULES:
1. Hebrew invoices are read RIGHT to LEFT. The columns ALWAYS appear in this exact order:
   RIGHT ➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔➔ LEFT
   [תיאור] ➔ [כמות] ➔ [מחיר יחידה] ➔ [סה"כ]
   [Description] ➔ [Quantity] ➔ [Unit Price] ➔ [Total]

2. COLUMN HEADERS TO LOOK FOR:
   - תיאור / פריט / שם פריט = Description
   - כמות = Quantity (ALWAYS the smaller number)
   - מחיר / מחיר יחידה = Unit Price
   - סה"כ / סכום = Total (ALWAYS quantity × price)

3. QUANTITY vs TOTAL DISAMBIGUATION RULES:
   a) כמות (Quantity) is ALWAYS:
      - The SMALLER number
      - Usually less than 100 units
      - When multiplied by price equals the total
   
   b) סה"כ (Total) is ALWAYS:
      - The LARGER number
      - Equal to quantity × price
      - Usually the rightmost number column

4. REAL EXAMPLES:
   Example 1: If you see:
   - מחיר יחידה (price) = 160.00
   - One number is 2.20
   - Other number is 352.00
   Then:
   - 2.20 MUST be כמות (quantity) because 2.20 × 160.00 = 352.00
   - 352.00 MUST be סה"כ (total)

   Example 2: If you see:
   - מחיר יחידה (price) = 38.00
   - One number is 266.00
   - Other number is 7.00
   Then:
   - 7.00 MUST be כמות (quantity) because 7.00 × 38.00 = 266.00
   - 266.00 MUST be סה"כ (total)

5. VALIDATION RULES:
   - ALWAYS verify: total = quantity × price
   - If the calculation doesn't match, you mapped the columns wrong
   - If total ÷ price gives a reasonable quantity (< 100), that's the correct mapping
   - Never accept a mapping where total ≠ quantity × price

Return this exact JSON structure:
{
    "company_details": {
        "name": "",
        "address": "",
        "tax_id": ""
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

FINAL VERIFICATION CHECKLIST:
1. Column order is correct (RTL: Description ➔ Quantity ➔ Price ➔ Total)
2. Quantity is ALWAYS the smaller number
3. Total is ALWAYS quantity × price
4. All calculations are verified
5. No null/None/undefined values
6. All numbers are actual numbers (not strings)
7. Subtotal = sum of all line totals
8. Tax = 17% of subtotal
9. Final total = subtotal + tax"""

async def process_with_timeout(model, prompt, image_parts, timeout=30):
    """Process with Gemini API using timeout."""
    try:
        start_time = time.time()
        
        # Create partial function for generate_content with optimized settings
        generate_func = partial(
            model.generate_content,
            [prompt, image_parts[0]],
            generation_config={
                'temperature': 0.1,    # Lower temperature for more focused results
                'top_p': 0.8,          # Reduce randomness
                'top_k': 40,           # Limit token choices
                'max_output_tokens': 800,   # Further reduced for faster processing
                'candidate_count': 1,   # Only need one response
            },
            timeout=timeout-2  # Leave 2 seconds for processing
        )
        
        # Run with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(generate_func)
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: future.result(timeout=timeout-1)  # Leave 1 second buffer
                )
                
                process_time = time.time() - start_time
                logger.info(f"Gemini API processing time: {process_time:.2f}s")
                
                # Debug log the raw response
                logger.info(f"Raw Gemini response length: {len(response.text)}")
                
                if not response or not hasattr(response, 'text'):
                    logger.error("Invalid response format from Gemini API")
                    raise Exception("Invalid response format from Gemini API")
                    
                if not response.text or not response.text.strip():
                    logger.error("Empty response text from Gemini API")
                    raise Exception("Empty response from Gemini API")
                
                return response
                
            except TimeoutError:
                process_time = time.time() - start_time
                logger.error(f"Gemini API timeout after {process_time:.2f}s")
                raise TimeoutError(f"Processing timed out after {process_time:.2f}s")
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(f"Gemini API error during generation after {process_time:.2f}s: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Error in process_with_timeout: {str(e)}")
        raise Exception(f"Processing error: {str(e)}")

def safe_float_convert(value: Union[str, int, float, None], field_name: str = "") -> float:
    """
    Safely convert a value to float with comprehensive error handling.
    
    Args:
        value: The value to convert
        field_name: Name of the field for logging purposes
    
    Returns:
        float: The converted value or 0.0 if conversion fails
    """
    try:
        if value is None or str(value).lower().strip() in ('none', 'null', '', 'undefined', 'nan'):
            logger.warning(f"Empty or None value for {field_name}, using 0.0")
            return 0.0
        
        if isinstance(value, (int, float)):
            return round(float(value), 2)
        
        # Clean the string value
        cleaned = str(value).strip()
        cleaned = re.sub(r'[^\d.-]', '', cleaned)
        
        if not cleaned:
            logger.warning(f"No numeric value found in '{value}' for {field_name}, using 0.0")
            return 0.0
        
        result = abs(float(cleaned))  # Convert to positive float
        return round(result, 2)
            
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not convert value '{value}' for {field_name}: {str(e)}, using 0.0")
        return 0.0

def create_empty_response() -> InvoiceData:
    """Create a valid empty response structure."""
    return {
        'company_details': {'name': '', 'address': '', 'tax_id': ''},
        'invoice_details': {'invoice_number': '', 'date': ''},
        'line_items': [],
        'totals': {'subtotal': 0.0, 'tax': 0.0, 'total': 0.0}
    }

def safe_json_response(data: Dict, status_code: int = 200) -> JsonResponse:
    """Create a safe JSON response with proper error handling."""
    try:
        return jsonify(data), status_code
    except Exception as e:
        logger.error(f"Error creating JSON response: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'details': str(e)
        }), 500

# Core Processing Functions
# -----------------------

def process_gemini_response(response_text: str) -> InvoiceData:
    """Process and validate Gemini's response with comprehensive error handling."""
    try:
        # Log the incoming response for debugging
        logger.info(f"Processing Gemini response: {response_text[:500]}...")  # Log first 500 chars
        
        # Clean and parse JSON response
        cleaned_text = response_text.strip()
        json_start = cleaned_text.find('{')
        json_end = cleaned_text.rfind('}')
        
        if json_start == -1 or json_end == -1:
            logger.error(f"No valid JSON object found in response: {cleaned_text}")
            return create_empty_response()
            
        json_text = cleaned_text[json_start:json_end + 1]
        logger.info(f"Extracted JSON text: {json_text[:500]}...")  # Log first 500 chars
        
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Attempted to parse: {json_text}")
            return create_empty_response()
        
        # Validate required structure
        if not isinstance(data, dict):
            logger.error(f"Response is not a dictionary: {type(data)}")
            return create_empty_response()
            
        required_keys = {'company_details', 'invoice_details', 'line_items', 'totals'}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            logger.error(f"Missing required keys in response: {missing_keys}")
            return create_empty_response()
        
        # Process line items with validation
        processed_items = []
        for idx, item in enumerate(data.get('line_items', [])):
            try:
                if not isinstance(item, dict):
                    logger.warning(f"Invalid line item format at index {idx}: {item}")
                    continue
                
                # Log raw values before conversion
                logger.info(f"Processing line item {idx}: {item}")
                
                # Extract and convert values
                quantity = safe_float_convert(item.get('quantity'), f'quantity_{idx}')
                price = safe_float_convert(item.get('price'), f'price_{idx}')
                total = safe_float_convert(item.get('total'), f'total_{idx}')
                
                # Verify calculations with logging
                calculated_total = round(quantity * price, 2)
                if abs(calculated_total - total) > 0.01:
                    logger.warning(
                        f"Total mismatch at index {idx}: "
                        f"quantity={quantity}, price={price}, "
                        f"calculated={calculated_total}, given={total}"
                    )
                    total = calculated_total
                
                processed_item = {
                    'item_code': str(item.get('item_code', '')),
                    'description': str(item.get('description', '')),
                    'quantity': quantity,
                    'price': price,
                    'total': total
                }
                logger.info(f"Processed line item {idx}: {processed_item}")
                processed_items.append(processed_item)
                
            except Exception as e:
                logger.error(f"Error processing line item {idx}: {str(e)}")
                continue
        
        # Calculate totals with validation
        subtotal = round(sum(item['total'] for item in processed_items), 2)
        tax = round(subtotal * 0.17, 2)  # 17% VAT
        total = round(subtotal + tax, 2)
        
        logger.info(f"Calculated totals: subtotal={subtotal}, tax={tax}, total={total}")
        
        result = {
            'company_details': {
                'name': str(data.get('company_details', {}).get('name', '')),
                'address': str(data.get('company_details', {}).get('address', '')),
                'tax_id': str(data.get('company_details', {}).get('tax_id', ''))
            },
            'invoice_details': {
                'invoice_number': str(data.get('invoice_details', {}).get('invoice_number', '')),
                'date': str(data.get('invoice_details', {}).get('date', ''))
            },
            'line_items': processed_items,
            'totals': {
                'subtotal': subtotal,
                'tax': tax,
                'total': total
            }
        }
        
        # Log final result
        logger.info("Successfully processed invoice data")
        return result
        
    except Exception as e:
        logger.error(f"Error processing Gemini response: {str(e)}")
        logger.error(f"Raw response: {response_text}")
        return create_empty_response()

# Routes and Request Handling
# -------------------------

@app.before_request
def before_request():
    """Handle CORS preflight requests."""
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # Ensure JSON content type for API endpoints
    if request.path.startswith(('/upload', '/save_changes', '/generate_report')):
        response.headers['Content-Type'] = 'application/json'
    
    return response

@app.route('/')
def index():
    """Serve the main application page with API status."""
    api_status = "active" if model else "inactive (API key not configured)"
    return render_template('index.html', api_status=api_status)

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests."""
    try:
        if os.path.exists('static/favicon.ico'):
            return app.send_static_file('favicon.ico')
        return '', 204
    except Exception as e:
        logger.error(f"Error serving favicon: {str(e)}")
        return '', 204

# Deployment-specific optimizations
VERCEL_DEPLOYMENT = os.getenv('VERCEL_REGION') is not None

if VERCEL_DEPLOYMENT:
    # Optimize for Vercel deployment
    logger.info("Running in Vercel environment - applying optimizations")
    
    # Reduce worker threads for Vercel
    ThreadPoolExecutor = lambda max_workers=None: ThreadPoolExecutor(max_workers=3)
    
    # Optimize image processing for Vercel
    def process_image_memory(file_data: bytes) -> List[Dict[str, str]]:
        """Process image data with Vercel-optimized settings."""
        try:
            from PIL import Image
            import io
            
            # Open image from bytes
            img = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Aggressive size reduction for Vercel
            max_size = (500, 500)  # Further reduced for Vercel
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Optimize image aggressively
            output = io.BytesIO()
            img.save(output, 
                    format='JPEG', 
                    quality=60,      # Further reduced quality for Vercel
                    optimize=True,
                    progressive=True
            )
            file_data = output.getvalue()
            
            logger.info(f"Vercel-optimized image size: {len(file_data) / 1024:.2f}KB")
            
            return [{
                "mime_type": "image/jpeg",
                "data": base64.b64encode(file_data).decode('utf-8')
            }]
        except Exception as e:
            logger.error(f"Vercel image processing error: {str(e)}")
            raise

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads with Firebase integration."""
    if not model:
        return safe_json_response({
            'status': 'error',
            'error': 'Gemini API is not configured'
        }, 503)
        
    try:
        start_time = time.time()
        
        # Check if we have a direct file upload or Firebase URL
        if 'firebase_url' in request.form:
            # Download from Firebase
            firebase_url = request.form['firebase_url']
            try:
                response = requests.get(firebase_url)
                response.raise_for_status()
                file_data = response.content
            except Exception as e:
                logger.error(f"Error downloading from Firebase: {str(e)}")
                return safe_json_response({
                    'status': 'error',
                    'error': f'Failed to download file from Firebase: {str(e)}'
                }, 400)
        elif 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return safe_json_response({'status': 'error', 'error': 'No selected file'}, 400)
            
            if not allowed_file(file.filename):
                return safe_json_response({'status': 'error', 'error': 'File type not allowed'}, 400)
            
            file_data = file.read()
        else:
            return safe_json_response({'status': 'error', 'error': 'No file provided'}, 400)

        # Process the file data
        try:
            file_size = len(file_data) / 1024
            logger.info(f"Processing file size: {file_size:.2f}KB")
            
            if len(file_data) > MAX_FILE_SIZE:
                return safe_json_response({
                    'status': 'error', 
                    'error': f'File too large ({file_size:.2f}KB > {MAX_FILE_SIZE/1024:.2f}KB)'
                }, 400)
            
            # Process image
            image_parts = process_image_memory(file_data)
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    response = loop.run_until_complete(
                        process_with_timeout(model, GEMINI_PROMPT, image_parts, timeout=30)
                    )
                    
                    if not response or not response.text:
                        raise Exception("Empty response from Gemini API")
                    
                    invoice_data = process_gemini_response(response.text)
                    
                    total_time = time.time() - start_time
                    logger.info(f"Total processing time: {total_time:.2f}s")
                    
                    return safe_json_response({
                        'status': 'success',
                        'invoice_data': invoice_data,
                        'processing_time': f"{total_time:.2f}s"
                    })
                    
                except TimeoutError as e:
                    logger.error(f"Processing timeout after {time.time() - start_time:.2f}s")
                    return safe_json_response({
                        'status': 'error',
                        'error': 'Processing timeout'
                    }, 408)
                    
                finally:
                    try:
                        loop.close()
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                return safe_json_response({
                    'status': 'error',
                    'error': str(e)
                }, 500)
                
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return safe_json_response({
                'status': 'error',
                'error': str(e)
            }, 500)
                
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return safe_json_response({
            'status': 'error',
            'error': str(e)
        }, 500)

@app.route('/save_changes', methods=['POST'])
def save_changes():
    """Save edited invoice data."""
    try:
        data = request.json
        return safe_json_response({'status': 'success'})
    except Exception as e:
        logger.error(f"Error saving changes: {str(e)}")
        return safe_json_response({
            'status': 'error',
            'error': str(e),
            'details': traceback.format_exc()
        }, 500)

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate comparison report between original and edited invoice data."""
    try:
        data = request.json
        if not data:
            return safe_json_response({'status': 'error', 'error': 'No data provided'}, 400)

        # Validate and extract data
        original_values = data.get('original_values', {})
        current_values = data.get('current_values', {})
        
        if not all(key in original_values for key in ['line_items', 'totals']):
            return safe_json_response({
                'status': 'error', 
                'error': 'Missing required fields in original_values'
            }, 400)

        if not all(key in current_values for key in ['line_items', 'totals']):
            return safe_json_response({
                'status': 'error', 
                'error': 'Missing required fields in current_values'
            }, 400)

        # Generate report
        report = {
            'line_items': {
                'original': original_values.get('line_items', []),
                'current': current_values.get('line_items', [])
            },
            'totals': {
                'original': original_values.get('totals', {'subtotal': 0, 'tax': 0, 'total': 0}),
                'current': current_values.get('totals', {'subtotal': 0, 'tax': 0, 'total': 0})
            },
            'changes': data.get('changes', []),
            'changes_by_item': data.get('changes_by_item', {}),
            'company_details': original_values.get('company_details', {}),
            'invoice_details': original_values.get('invoice_details', {})
        }

        return safe_json_response({
            'status': 'success',
            'report': report
        })

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return safe_json_response({
            'status': 'error',
            'error': str(e),
            'details': traceback.format_exc()
        }, 500)

@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    return jsonify({
        'status': 'healthy',
        'gemini': 'active' if model else 'inactive',
        'timestamp': time.time()
    })

# Error Handlers
# -------------

@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler for unhandled exceptions."""
    logger.error(f"Unhandled error: {str(e)}")
    return safe_json_response({
        'status': 'error',
        'error': str(e),
        'details': traceback.format_exc()
    }, 500)

# Vercel Serverless Configuration
# -----------------------------

def create_app():
    """Create Flask app for Vercel."""
    return app

# Vercel requires this
app.create_app = create_app

# Main Entry Point (for local development)
# --------------------------------------

if __name__ == '__main__':
    # Development settings
    app.run(
        host='127.0.0.1',
        port=int(os.getenv('PORT', 5000)),
        debug=False
    )