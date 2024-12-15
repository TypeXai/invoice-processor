from app import app
from flask import request, jsonify

def application(environ, start_response):
    """WSGI application"""
    return app(environ, start_response)

def handler(event, context):
    """Vercel serverless function handler"""
    try:
        return app.handle_request()
    except Exception as e:
        app.logger.error(f"Error handling request: {str(e)}")
        response = jsonify({
            'status': 'error',
            'error': str(e)
        })
        response.status_code = 500
        return response

# For local development
if __name__ == '__main__':
    app.run() 