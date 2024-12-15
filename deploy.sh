#!/bin/bash

# Build and deploy to Cloud Run
echo "Building and deploying to Cloud Run..."
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/invoice-processor

# Deploy to Cloud Run
gcloud run deploy invoice-processor \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/invoice-processor \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 120 \
  --set-env-vars "GOOGLE_API_KEY=$GOOGLE_API_KEY" \
  --allow-unauthenticated

# Deploy Firebase hosting
echo "Deploying Firebase hosting..."
firebase deploy --only hosting

echo "Deployment complete! Your app should be available at:"
gcloud run services describe invoice-processor --platform managed --region us-central1 --format 'value(status.url)' 