# Invoice Processing Application with Gemini Vision AI

A modern web application for processing and analyzing invoices using Google's Gemini Vision AI. The application supports RTL (Right-to-Left) text and is optimized for Hebrew invoices.

## Deployment to Vercel

### Prerequisites

- Vercel account
- Google Cloud account with Gemini API access
- Git repository

### Environment Variables Setup

1. In Vercel project settings, add these environment variables:
   ```
   GOOGLE_API_KEY=your-gemini-api-key
   MAX_FILE_SIZE=16777216
   ALLOWED_EXTENSIONS=png,jpg,jpeg
   PYTHONUNBUFFERED=1
   PYTHON_VERSION=3.9
   UPLOAD_FOLDER=/tmp/uploads
   FLASK_ENV=production
   FLASK_DEBUG=0
   ```

### Deployment Steps

1. Install Vercel CLI:

   ```bash
   npm i -g vercel
   ```

2. Login to Vercel:

   ```bash
   vercel login
   ```

3. Deploy:
   ```bash
   vercel --prod
   ```

### Post-Deployment Checks

1. Verify environment variables are set correctly
2. Test file upload functionality
3. Verify Gemini API integration
4. Check invoice processing workflow
5. Verify RTL text rendering
6. Test change tracking and reporting

### Monitoring

- Use Vercel's built-in monitoring
- Check function execution logs
- Monitor API rate limits
- Watch for memory usage

### Troubleshooting

- Check Vercel function logs for errors
- Verify environment variables
- Check file upload size limits
- Monitor Gemini API quotas

## Features

- Upload and process PNG and JPG invoices
- Automatic text extraction using Gemini Vision AI
- Real-time invoice editing with automatic calculations
- RTL support for Hebrew text
- Change tracking and detailed reporting
- Print-friendly output

## Local Development

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/invoice-processor.git
   cd invoice-processor
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. Run development server:
   ```bash
   python app.py
   ```

## Security Considerations

- API keys are stored securely in environment variables
- File uploads are validated and sanitized
- Temporary files are cleaned up after processing
- CORS settings are configured for security
- Memory limits are set to prevent abuse

## Maintenance

1. Regular Updates

   - Check for package updates
   - Monitor Gemini API version changes
   - Update security patches

2. Backup

   - Regular database backups (if added)
   - Configuration backups
   - Environment variable documentation

3. Monitoring
   - Set up alerts for errors
   - Monitor API usage
   - Track performance metrics

## License

MIT License - see LICENSE file for details
