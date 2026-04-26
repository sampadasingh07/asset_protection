@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "COMPOSE_FILE=%PROJECT_ROOT%backend\docker-compose.yml"

if not exist "%COMPOSE_FILE%" (
  echo [ERROR] Compose file not found: %COMPOSE_FILE%
  exit /b 1
)

set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=start"

if /I "%ACTION%"=="start" goto start
if /I "%ACTION%"=="rebuild" goto rebuild
if /I "%ACTION%"=="stop" goto stop
if /I "%ACTION%"=="status" goto status
if /I "%ACTION%"=="logs" goto logs

echo Usage: %~n0 ^<start^|rebuild^|stop^|status^|logs^>
echo Example: %~n0 start
exit /b 1

:start
echo [INFO] Starting Docker stack...
docker compose -f "%COMPOSE_FILE%" up -d --no-build postgres redis backend worker frontend
if errorlevel 1 exit /b %errorlevel%
docker compose -f "%COMPOSE_FILE%" ps
exit /b 0

:rebuild
echo [INFO] Rebuilding and starting Docker stack...
docker compose -f "%COMPOSE_FILE%" up -d --build --force-recreate postgres redis backend worker frontend
if errorlevel 1 exit /b %errorlevel%
docker compose -f "%COMPOSE_FILE%" ps
exit /b 0

:stop
echo [INFO] Stopping Docker stack...
docker compose -f "%COMPOSE_FILE%" down
exit /b %errorlevel%

:status
docker compose -f "%COMPOSE_FILE%" ps -a
exit /b %errorlevel%

:logs
docker compose -f "%COMPOSE_FILE%" logs -f --tail=100
exit /b %errorlevel%
