# One-click publish script.
# Double-click this file (or run: powershell -ExecutionPolicy Bypass -File publish.ps1)
#
# It signs you in to GitHub, then creates the PUBLIC repository and pushes
# the project. Everything after the login is automatic.

$ErrorActionPreference = 'Stop'

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Make sure gh and git are reachable even in an old console window.
$ghBin    = Join-Path $env:LOCALAPPDATA 'Programs\GitHub CLI\bin'
$gitHubDesktop = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'GitHubDesktop') `
    -Directory -Filter 'app-*' -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1
$gitCmd = if ($gitHubDesktop) { Join-Path $gitHubDesktop.FullName 'resources\app\git\cmd' } else { $null }

foreach ($dir in @($ghBin, $gitCmd)) {
    if ($dir -and (Test-Path -LiteralPath $dir)) {
        if ($env:Path -notlike "*$dir*") { $env:Path = "$dir;$env:Path" }
    }
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host 'ERROR: the GitHub CLI (gh) was not found.' -ForegroundColor Red
    Write-Host "Expected it in: $ghBin"
    Read-Host 'Press Enter to close'
    exit 1
}

Set-Location -LiteralPath $projectDir

$repoName = 'tarot-football-predictor'
$repoDesc = 'Football predictor combining a 78-card tarot spread with Pythagorean and Chaldean numerology. Python, CLI and Streamlit UI.'

# Open the authorisation page in Brave instead of the Windows default (Edge).
$braveCandidates = @(
    (Join-Path $env:ProgramFiles 'BraveSoftware\Brave-Browser\Application\brave.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'BraveSoftware\Brave-Browser\Application\brave.exe'),
    (Join-Path $env:LOCALAPPDATA 'BraveSoftware\Brave-Browser\Application\brave.exe')
)
$brave = $braveCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1

if ($brave) {
    $env:GH_BROWSER = $brave
    Write-Host "Browser: Brave ($brave)" -ForegroundColor DarkGray
} else {
    Write-Host 'Browser: system default (Brave not found)' -ForegroundColor DarkGray
    Write-Host 'Set $env:GH_BROWSER manually if Edge opens instead.' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '=== STEP 1 of 2: signing in to GitHub ===' -ForegroundColor Cyan
Write-Host 'The one-time code is copied to your clipboard automatically.'
Write-Host 'Paste it into the GitHub page, then click "Authorize github".'
Write-Host ''

# --clipboard copies the one-time code so it never has to be read off the screen.
& gh auth login --hostname github.com --git-protocol https --web --clipboard --skip-ssh-key
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Sign-in was cancelled or failed. Nothing was published.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}

Write-Host ''
Write-Host '=== STEP 2 of 2: creating the public repository ===' -ForegroundColor Cyan

# Read the real account name from GitHub rather than assuming one.
$login = (& gh api user --jq .login 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $login) {
    Write-Host 'Could not read your GitHub username after sign-in.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}
$login = $login.Trim()
$repoUrl = "https://github.com/$login/$repoName"
Write-Host "Signed in as: $login"
Write-Host "Target repo : $repoUrl"
Write-Host ''

# If the repo already exists, wire it up instead of failing.
& gh repo view $repoUrl 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host 'That repository already exists - pushing to it instead of creating a new one.'
    if (-not (& git remote 2>$null | Select-String -SimpleMatch 'origin')) {
        & git remote add origin $repoUrl
    }
    & git push -u origin main
} else {
    & gh repo create $repoUrl `
        --public `
        --description $repoDesc `
        --source $projectDir `
        --remote origin `
        --push
}

if ($LASTEXITCODE -ne 0) {
    Write-Host 'Something went wrong during the push.' -ForegroundColor Red
    Write-Host 'The code is committed locally, so nothing is lost.'
    Read-Host 'Press Enter to close'
    exit 1
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host ' PUBLISHED SUCCESSFULLY' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Write-Host " Link: $repoUrl"
Write-Host ''
Read-Host 'Press Enter to close'