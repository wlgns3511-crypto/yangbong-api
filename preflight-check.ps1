# ===== Preflight (ASCII/PowerShell-safe) =====
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "== Preflight ==" -ForegroundColor Cyan

# 1) Tools
$tools = @("git","py","node","npm")
foreach ($t in $tools) {
  if (Get-Command $t -ErrorAction SilentlyContinue) {
    try { $ver = & $t --version 2>$null } catch { $ver = "(version check failed)" }
    Write-Host ("OK   {0,-5} : {1}" -f $t, $ver) -ForegroundColor Green
  } else {
    Write-Host ("MISS {0,-5} : not installed" -f $t) -ForegroundColor Red
  }
}

# 2) Execution policy
$pol = Get-ExecutionPolicy -Scope CurrentUser
Write-Host ("Policy(CurrentUser): {0}" -f $pol)
if ($pol -ne "RemoteSigned") {
  Write-Host "WARN: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned (recommended)"
}

# 3) Network 443 tests
$hosts = "google.com","github.com","pypi.org","registry.npmjs.org","api.openai.com"
foreach ($h in $hosts) {
  $ok = Test-NetConnection $h -Port 443 -InformationLevel Quiet
  if ($ok) {
    Write-Host ("NET  {0,-18} : OK" -f $h) -ForegroundColor Green
  } else {
    Write-Host ("NET  {0,-18} : FAIL" -f $h) -ForegroundColor Red
  }
}

# 4) Ports 3000/8000
foreach ($p in 3000,8000) {
  $conn = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
  if ($conn) {
    $pid = ($conn | Select -Expand OwningProcess -Unique)
    Write-Host ("PORT {0} : IN-USE (PID {1})" -f $p,$pid) -ForegroundColor Yellow
  } else {
    Write-Host ("PORT {0} : FREE" -f $p) -ForegroundColor Green
  }
}

# 5) SSH key
$key = "$env:USERPROFILE\.ssh\id_ed25519.pub"
if (Test-Path $key) {
  Write-Host ("SSH  key : FOUND -> {0}" -f $key) -ForegroundColor Green
} else {
  Write-Host "SSH  key : NOT FOUND (run: ssh-keygen -t ed25519 -C 'you@example.com')" -ForegroundColor Yellow
}

Write-Host "== Done ==" -ForegroundColor Cyan
