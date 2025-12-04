#!/bin/bash
# Build script for Render deployment

echo "🚀 Starting build process..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Apply database migration
echo "🗄️ Applying database migrations..."
python3 apply_migration.py

echo "✅ Build completed successfully!"
