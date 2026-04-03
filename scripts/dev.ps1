param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("up", "down", "logs", "test", "test-auth", "migrate", "lint", "format", "check-format")]
    [string]$Command
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

switch ($Command) {
    "up" {
        docker compose -f docker-compose-dev.yaml up --build
    }
    "down" {
        docker compose -f docker-compose-dev.yaml down
    }
    "logs" {
        docker compose -f docker-compose-dev.yaml logs -f api
    }
    "test" {
        cmd /c "set PYTHONPATH=.&& .venv\Scripts\pytest.exe -q"
    }
    "test-auth" {
        cmd /c "set PYTHONPATH=.&& .venv\Scripts\pytest.exe tests/features/auth -q"
    }
    "migrate" {
        .venv\Scripts\alembic.exe upgrade head
    }
    "lint" {
        .venv\Scripts\ruff.exe check app tests
    }
    "format" {
        .venv\Scripts\ruff.exe check app tests --fix
        .venv\Scripts\black.exe app tests
    }
    "check-format" {
        .venv\Scripts\black.exe --check app tests
    }
}
