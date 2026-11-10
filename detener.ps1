# Apaga el túnel, la aplicación y Neo4j de UniRed.
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
foreach ($p in 8000, 7687, 7474) {
    Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Write-Host "UniRed apagado."
