if (!((Test-Path ".\docker\web\.env.dev.web") -and (Test-Path ".\docker\db\.env.dev.db") -and (Test-Path ".\docker\worker\.env.dev.worker"))) {
    Write-Host "Error: Missing docker/web/.env.dev.web, docker/db/.env.deb.db, or docker/worker/.env.dev.worker."
    Exit
}

docker-compose -f .\docker\docker-compose.yml up --build --detach

Write-Host "You can now access the web server at http://127.0.0.1:8000/"