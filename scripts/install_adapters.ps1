#Requires -Version 5.1
param(
  [ValidateSet('all','codex','claude','hermes','trae','zcode','doubao')]
  [string[]]$Targets = @('all'),
  [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$Source = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$HomeDir = [Environment]::GetFolderPath('UserProfile')

$Map = [ordered]@{
  codex = Join-Path $HomeDir '.codex\skills'
  claude = Join-Path $HomeDir '.claude\skills'
  hermes = Join-Path $HomeDir 'AppData\Local\hermes\skills'
  trae = Join-Path $HomeDir '.trae-cn\skills'
  zcode = Join-Path $HomeDir '.zcode\skills'
}

if ($Targets -contains 'all') { $Targets = @('codex','claude','hermes','trae','zcode') }

foreach ($target in $Targets) {
  if ($target -eq 'doubao') {
    $doubaoRoot = Join-Path $HomeDir 'Doubao\skills'
    if (Test-Path -LiteralPath (Split-Path $doubaoRoot -Parent)) {
      if (-not (Test-Path -LiteralPath $doubaoRoot)) { New-Item -ItemType Directory -Path $doubaoRoot | Out-Null }
      $dest = Join-Path $doubaoRoot 'card-code-recharge-bridge.md'
      if ($WhatIf) { Write-Host "Would copy doubao prompt -> $dest" }
      else { Copy-Item -LiteralPath (Join-Path $Source 'adapters\doubao-prompt-pack.md') -Destination $dest -Force }
    }
    continue
  }

  $skillsRoot = $Map[$target]
  if (-not $skillsRoot) { continue }
  if (-not (Test-Path -LiteralPath (Split-Path $skillsRoot -Parent))) {
    Write-Warning "Skip ${target}: parent directory not found: $skillsRoot"
    continue
  }
  if (-not (Test-Path -LiteralPath $skillsRoot)) {
    if ($WhatIf) { Write-Host "Would create $skillsRoot" }
    else { New-Item -ItemType Directory -Path $skillsRoot | Out-Null }
  }
  $dest = Join-Path $skillsRoot 'card-code-recharge-bridge'
  if ($WhatIf) {
    Write-Host "Would copy $Source -> $dest"
  } else {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    $items = @('SKILL.md','README.md','README.zh-CN.md','LICENSE','SECURITY.md','CONTRIBUTING.md','CHANGELOG.md','agents','scripts','references','assets','adapters')
    foreach ($item in $items) {
      $srcItem = Join-Path $Source $item
      if (-not (Test-Path -LiteralPath $srcItem)) { continue }
      if (Test-Path -LiteralPath $srcItem -PathType Leaf) {
        Copy-Item -LiteralPath $srcItem -Destination (Join-Path $dest $item) -Force
        continue
      }
      Get-ChildItem -LiteralPath $srcItem -Recurse -File |
        Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' } |
        ForEach-Object {
          $relative = $_.FullName.Substring($srcItem.Length).TrimStart([char[]]@('\','/'))
          $targetPath = Join-Path (Join-Path $dest $item) $relative
          $targetDir = Split-Path $targetPath -Parent
          New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
          Copy-Item -LiteralPath $_.FullName -Destination $targetPath -Force
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $dest 'SKILL.md'))) {
      throw "Install verification failed for ${target}: $dest\SKILL.md"
    }
    # 清理旧版安装可能留下的嵌套副本，避免同一 Skill 被识别两次。
    $nestedSkill = Join-Path $dest 'card-code-recharge-bridge\SKILL.md'
    if (Test-Path -LiteralPath $nestedSkill) {
      $nestedDisabled = Join-Path (Split-Path $nestedSkill -Parent) 'SKILL.md.disabled'
      if (-not (Test-Path -LiteralPath $nestedDisabled)) {
        Rename-Item -LiteralPath $nestedSkill -NewName 'SKILL.md.disabled'
      }
    }
    Write-Host "Installed: $dest"
  }
}



