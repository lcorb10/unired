# UniRed: enciende Neo4j, la aplicación y el túnel público, todo en segundo plano.
# Uso: doble clic en iniciar.bat (o .\iniciar.ps1). Para apagar: detener.bat
$ErrorActionPreference = "Stop"
$raiz   = Split-Path -Parent $MyInvocation.MyCommand.Path
$app    = Join-Path $raiz "app"
$local  = "D:\neo4j_local"
$neo4j  = Join-Path $local "neo4j-community-5.26.0"
$java   = Get-ChildItem $local -Directory -Filter "jdk-*" | Select-Object -First 1
$logs   = Join-Path $local "logs"
New-Item -ItemType Directory -Force $logs | Out-Null

function Escucha($puerto) { [bool](Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue) }

Write-Host "UniRed: encendiendo..." -ForegroundColor Red

# 1. Neo4j (puerto 7687)
if (-not (Escucha 7687)) {
    $env:JAVA_HOME = $java.FullName
    Start-Process -FilePath (Join-Path $neo4j "bin\neo4j.bat") -ArgumentList "console" -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logs "neo4j.log") -RedirectStandardError (Join-Path $logs "neo4j.err")
    Write-Host -NoNewline "  Neo4j "
    for ($i = 0; $i -lt 60 -and -not (Escucha 7687); $i++) { Start-Sleep 2; Write-Host -NoNewline "." }
    Write-Host " listo"
} else { Write-Host "  Neo4j ya estaba encendido" }

# 2. Aplicación (waitress, puerto 8000)
if (-not (Escucha 8000)) {
    Start-Process -FilePath (Join-Path $app "venv\Scripts\python.exe") -ArgumentList "servidor.py" -WorkingDirectory $app `
        -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs "unired.log") -RedirectStandardError (Join-Path $logs "unired.err")
    for ($i = 0; $i -lt 30 -and -not (Escucha 8000); $i++) { Start-Sleep 1 }
    Write-Host "  App lista en http://127.0.0.1:8000"
} else { Write-Host "  La app ya estaba encendida" }

# 3. Túnel público de Cloudflare (el link cambia cada vez que se enciende)
$tunelLog = Join-Path $logs "tunel.log"
if (-not (Get-Process cloudflared -ErrorAction SilentlyContinue)) {
    if (Test-Path $tunelLog) { Remove-Item $tunelLog }
    Start-Process -FilePath (Join-Path $local "cloudflared.exe") -ArgumentList "tunnel --no-autoupdate --url http://127.0.0.1:8000" `
        -WindowStyle Hidden -RedirectStandardError $tunelLog -RedirectStandardOutput (Join-Path $logs "tunel.out")
}
$url = $null
for ($i = 0; $i -lt 40 -and -not $url; $i++) {
    Start-Sleep 1
    if (Test-Path $tunelLog) {
        $m = Select-String -Path $tunelLog -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
        if ($m) { $url = $m.Matches[0].Value }
    }
}
if ($url) {
    Set-Content -Path (Join-Path $raiz "LINK_PUBLICO.txt") -Value $url
    Set-Clipboard -Value $url
    Write-Host ""
    Write-Host "  Link público (copiado al portapapeles):" -ForegroundColor Yellow
    Write-Host "  $url" -ForegroundColor Yellow
} else {
    Write-Host "  No se obtuvo el link del túnel. Revisa $tunelLog" -ForegroundColor Red
}
Write-Host ""
Write-Host "  Neo4j Browser: http://localhost:7474  (usuario neo4j)"
Write-Host "  Para apagar todo: detener.bat"
