# Simple demo runner for local development (PowerShell)
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)
Set-Location ..
python manage.py migrate --noinput
Start-Process -NoNewWindow -FilePath python -ArgumentList 'manage.py runserver'
Push-Location frontend
npm run preview
Pop-Location