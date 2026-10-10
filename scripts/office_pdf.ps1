param(
    [Parameter(Mandatory=$true)][ValidateSet('pptx','docx')][string]$Kind,
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference = 'Stop'
$application = $null
$document = $null
$processName = if ($Kind -eq 'pptx') { 'POWERPNT' } else { 'WINWORD' }
$wasRunning = @(Get-Process $processName -ErrorAction SilentlyContinue).Count -gt 0
try {
    if ($Kind -eq 'pptx') {
        $application = New-Object -ComObject PowerPoint.Application
        $document = $application.Presentations.Open($Source, -1, 0, 0)
        $document.SaveAs($Destination, 32)
    } else {
        $application = New-Object -ComObject Word.Application
        $document = $application.Documents.Open($Source, $false, $true, $false)
        $document.ExportAsFixedFormat($Destination, 17)
    }
} finally {
    if ($null -ne $document) {
        $document.Close()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    }
    # Never quit an Office application that the user already had open.
    if ($null -ne $application) {
        if (-not $wasRunning) {
            try { $application.Quit() }
            catch {
                # Word can exit itself after its last automation document closes.
                if ($_.Exception.ToString() -notmatch '0x800706BA') { throw }
            }
        }
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($application)
    }
}
