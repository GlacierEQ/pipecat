#!/bin/bash
# Generate self-signed SSL certificates for local development

# Set default values
DOMAIN="pipecat.example.com"
DASHBOARD_DOMAIN="dashboard.pipecat.example.com"
API_DOMAIN="api.pipecat.example.com"
SSL_DIR="./nginx/ssl"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Generate SSL certificate for the main domain
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/$DOMAIN.key" \
    -out "$SSL_DIR/$DOMAIN.crt" \
    -subj "/CN=$DOMAIN"

# Generate SSL certificate for the dashboard subdomain
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/$DASHBOARD_DOMAIN.key" \
    -out "$SSL_DIR/$DASHBOARD_DOMAIN.crt" \
    -subj "/CN=$DASHBOARD_DOMAIN"

# Generate SSL certificate for the API subdomain
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/$API_DOMAIN.key" \
    -out "$SSL_DIR/$API_DOMAIN.crt" \
    -subj "/CN=$API_DOMAIN"

echo "SSL certificates generated in $SSL_DIR"
