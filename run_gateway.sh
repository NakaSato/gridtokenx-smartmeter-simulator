#!/bin/bash
# Launcher for API Gateway to solve path issues
cd /Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-apigateway
export DATABASE_URL="postgresql://gridtokenx_user:gridtokenx_password@localhost:5432/gridtokenx"
export REDIS_URL="redis://localhost:6379"
# The app uses dotenvy, so it will pick up the rest from .env in the current directory (gridtokenx-apigateway)
exec ../target/debug/api-gateway
