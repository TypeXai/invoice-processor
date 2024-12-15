# Invoice Processing Application with Gemini Vision AI

Modern invoice processing application that uses Google's Gemini Vision AI to extract and edit invoice data, with support for Hebrew RTL invoices.

## Features

- PDF, Image (PNG, JPG) invoice processing
- Hebrew (RTL) invoice support
- Real-time invoice editing
- Change tracking and comparison
- PDF and Excel report generation
- Mobile-responsive design

## Tech Stack

- Backend: Flask + Gemini Vision AI
- Frontend: HTML5, CSS3, JavaScript
- Database: File-based storage
- Deployment: Firebase Hosting + Cloud Functions

## Local Development Setup

1. Clone the repository:

```bash
git clone [repository-url]
cd invoice-processing-app
```

2. Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY and other settings
```

5. Run the development server:

```bash
python app.py
```

## Deployment

### Firebase Deployment

1. Install Firebase CLI:

```bash
npm install -g firebase-tools
```

2. Login to Firebase:

```bash
firebase login
```

3. Initialize Firebase project:

```bash
firebase init
```

4. Deploy:

```bash
firebase deploy
```

## Project Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/               # Static assets
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── fonts/           # Custom fonts
├── templates/            # HTML templates
├── uploads/             # Temporary file storage
└── functions/           # Firebase Cloud Functions
```

## Environment Variables

Required in .env file:

```
GOOGLE_API_KEY=your-gemini-api-key
FLASK_ENV=development
FLASK_APP=app.py
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
