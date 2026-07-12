#!/bin/bash

# ==============================================================================
# SPLASHBot Backend Deployment Script
# ==============================================================================

GREEN='\033[0;32m'
NC='\033[0m'
RED='\033[0;31m'
YELLOW='\033[1;33m'

echo -e "${GREEN}=== Memulai Deploy Backend SPLASHBot ===${NC}"

# Validasi Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker tidak ditemukan.${NC}"
    exit 1
fi

# Tentukan command docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}Error: Docker Compose tidak ditemukan.${NC}"
    exit 1
fi

# Validasi file .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Peringatan: File .env tidak ditemukan! Harap siapkan sebelum menjalankan.${NC}"
fi

# Build dan jalankan backend (Zero-downtime redeploy)
echo -e "${GREEN}Membangun (jika ada perubahan) dan menjalankan kontainer backend...${NC}"
$DOCKER_COMPOSE up --build -d

echo -e "${GREEN}=== Backend Deployment Selesai ===${NC}"
$DOCKER_COMPOSE ps
echo -e "Backend berjalan secara lokal di port: ${YELLOW}8000${NC}"
