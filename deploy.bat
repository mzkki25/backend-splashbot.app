@echo off
echo ==============================================================================
echo Memulai Deploy Backend SPLASHBot (Windows)
echo ==============================================================================

:: Cek apakah Docker terpasang
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Docker tidak ditemukan. Harap instal Docker terlebih dahulu.
    pause
    exit /b 1
)

:: Tentukan command docker compose
docker compose version >nul 2>nul
if %errorlevel% equ 0 (
    set DOCKER_COMPOSE=docker compose
) else (
    where docker-compose >nul 2>nul
    if %errorlevel% equ 0 (
        set DOCKER_COMPOSE=docker-compose
    ) else (
        echo Error: Docker Compose tidak ditemukan. Harap instal Docker Compose.
        pause
        exit /b 1
    )
)

:: Cek file .env
if not exist .env (
    echo Peringatan: File .env tidak ditemukan! Harap siapkan sebelum menjalankan.
)

echo Membangun dan menjalankan kontainer backend...
%DOCKER_COMPOSE% up --build -d

echo ==============================================================================
echo Backend Deployment Selesai!
echo ==============================================================================
%DOCKER_COMPOSE% ps
echo Backend berjalan secara lokal di port: 8000
