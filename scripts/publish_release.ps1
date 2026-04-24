param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl,

    [string]$Branch = "main",
    [string]$Tag = "v0.1.0",
    [string]$CommitMessage = "chore: prepare open-source alpha release"
)

$ErrorActionPreference = "Stop"

function Run-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    Write-Host "git $($Args -join ' ')"
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed: git $($Args -join ' ')"
    }
}

if (-not (Test-Path ".git")) {
    throw "Current directory is not a git repository."
}

$remoteExists = $false
try {
    & git remote get-url origin *> $null
    $remoteExists = ($LASTEXITCODE -eq 0)
} catch {
    $remoteExists = $false
}

if ($remoteExists) {
    Run-Git -Args @("remote", "set-url", "origin", $RemoteUrl)
} else {
    Run-Git -Args @("remote", "add", "origin", $RemoteUrl)
}

Run-Git -Args @("add", ".")

$hasDiff = $false
& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    $hasDiff = $true
}

if ($hasDiff) {
    Run-Git -Args @("commit", "-m", $CommitMessage)
} else {
    Write-Host "No staged changes to commit."
}

Run-Git -Args @("push", "-u", "origin", $Branch)

$tagExists = $false
& git rev-parse $Tag *> $null
if ($LASTEXITCODE -eq 0) {
    $tagExists = $true
}

if (-not $tagExists) {
    Run-Git -Args @("tag", $Tag)
}

Run-Git -Args @("push", "origin", $Tag)

Write-Host ""
Write-Host "Release publish flow finished."
Write-Host "Suggested GitHub release notes source:"
Write-Host "docs/GITHUB_RELEASE_v0.1.0.md"

