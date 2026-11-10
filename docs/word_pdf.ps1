# Abre el .docx con Word (invisible), actualiza la tabla de contenido, guarda y exporta a PDF.
param([string]$Docx)
$ErrorActionPreference = "Stop"
$ruta = (Resolve-Path $Docx).Path
$pdf = [System.IO.Path]::ChangeExtension($ruta, ".pdf")
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($ruta, $false, $false)
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    $doc.Fields.Update() | Out-Null
    $doc.Save()
    $doc.ExportAsFixedFormat($pdf, 17)
    Write-Host "Paginas:" $doc.ComputeStatistics(2)
    $doc.Close($false)
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
Write-Host "PDF:" $pdf
