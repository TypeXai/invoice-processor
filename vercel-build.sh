#!/bin/bash

# Create lib directory
mkdir -p .vercel/lib

# Download and extract libjpeg
curl -L https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/2.1.4/libjpeg-turbo-2.1.4-linux-x64.tar.gz | tar xz -C .vercel/

# Copy the library files
cp .vercel/libjpeg-turbo-2.1.4-linux-x64/lib/libjpeg.so.62 .vercel/lib/
cp .vercel/libjpeg-turbo-2.1.4-linux-x64/lib/libturbojpeg.so.0 .vercel/lib/

# Clean up
rm -rf .vercel/libjpeg-turbo-2.1.4-linux-x64

# Make the script executable
chmod +x .vercel/lib/libjpeg.so.62
chmod +x .vercel/lib/libturbojpeg.so.0 