$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression.FileSystem

$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePath = Join-Path $workspace '4月竞赛参考题库.xlsx'
$templatePath = Join-Path $workspace '题库1_标准化.xlsx'
$outputPath = Join-Path $workspace '4月竞赛参考题库_标准化.xlsx'

$standardHeaders = @(
    '题型',
    '题干',
    '选项A',
    '选项B',
    '选项C',
    '选项D',
    '选项E',
    '选项F',
    '正确答案',
    '分值',
    '来源题库',
    '题目难度'
)

$typeMapping = @{
    '单选题' = '单选'
    '多选题' = '多选'
    '判断题' = '判断'
    '问答题' = '简答'
}

function Resolve-ZipEntry {
    param(
        [System.IO.Compression.ZipArchive]$Zip,
        [string]$Target
    )

    $candidates = @($Target, $Target.TrimStart('/'))
    if ($Target -notmatch '^xl/') {
        $candidates += ('xl/' + $Target.TrimStart('/'))
    }

    foreach ($candidate in $candidates) {
        $entry = $Zip.Entries | Where-Object { $_.FullName -eq $candidate } | Select-Object -First 1
        if ($entry) {
            return $entry
        }
    }

    return $null
}

function Get-CellValue {
    param(
        $Cell,
        [string[]]$SharedStrings
    )

    if ($null -eq $Cell) {
        return ''
    }

    if ($Cell.t -eq 's') {
        return $SharedStrings[[int]$Cell.v]
    }

    if ($Cell.is -and $Cell.is.t) {
        return [string]$Cell.is.t
    }

    if ($Cell.is -and $Cell.is.r) {
        return (($Cell.is.r | ForEach-Object { $_.t }) -join '')
    }

    return [string]$Cell.v
}

function Read-FirstWorksheetRows {
    param([string]$Path)

    $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $sharedStrings = @()
        $sharedEntry = Resolve-ZipEntry -Zip $zip -Target 'xl/sharedStrings.xml'
        if ($sharedEntry) {
            $reader = New-Object System.IO.StreamReader($sharedEntry.Open())
            $sharedXml = [xml]$reader.ReadToEnd()
            $reader.Close()

            foreach ($si in $sharedXml.sst.si) {
                if ($si.t) {
                    $sharedStrings += [string]$si.t
                }
                elseif ($si.r) {
                    $sharedStrings += (($si.r | ForEach-Object { $_.t }) -join '')
                }
                else {
                    $sharedStrings += ''
                }
            }
        }

        $workbookReader = New-Object System.IO.StreamReader((Resolve-ZipEntry -Zip $zip -Target 'xl/workbook.xml').Open())
        $workbookXml = [xml]$workbookReader.ReadToEnd()
        $workbookReader.Close()

        $relsReader = New-Object System.IO.StreamReader((Resolve-ZipEntry -Zip $zip -Target 'xl/_rels/workbook.xml.rels').Open())
        $relsXml = [xml]$relsReader.ReadToEnd()
        $relsReader.Close()

        $sheet = $workbookXml.workbook.sheets.sheet | Select-Object -First 1
        $rid = $sheet.GetAttribute('id', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
        $sheetTarget = ($relsXml.Relationships.Relationship | Where-Object { $_.Id -eq $rid }).Target

        $sheetReader = New-Object System.IO.StreamReader((Resolve-ZipEntry -Zip $zip -Target $sheetTarget).Open())
        $sheetXml = [xml]$sheetReader.ReadToEnd()
        $sheetReader.Close()

        $rows = @()
        foreach ($row in $sheetXml.worksheet.sheetData.row) {
            $rowMap = @{}
            foreach ($cell in $row.c) {
                $column = [regex]::Match($cell.r, '^[A-Z]+').Value
                $rowMap[$column] = Get-CellValue -Cell $cell -SharedStrings $sharedStrings
            }
            $rows += [pscustomobject]@{
                Index = [int]$row.r
                Cells = $rowMap
            }
        }

        return $rows
    }
    finally {
        $zip.Dispose()
    }
}

function Normalize-Answer {
    param(
        [string]$QuestionType,
        [string]$Answer
    )

    $answerText = ($Answer | ForEach-Object { $_.ToString().Trim() })

    switch ($QuestionType) {
        '判断' {
            if ($answerText -match '^(A|对|正确)$') { return 'A' }
            if ($answerText -match '^(B|错|错误)$') { return 'B' }
            return $answerText
        }
        '多选' {
            $letters = [regex]::Matches($answerText.ToUpperInvariant(), '[A-F]') | ForEach-Object { $_.Value }
            $distinct = $letters | Sort-Object -Unique
            return ($distinct -join '')
        }
        default {
            $letter = [regex]::Match($answerText.ToUpperInvariant(), '[A-F]').Value
            if ($letter) { return $letter }
            return $answerText
        }
    }
}

function Escape-XmlText {
    param([string]$Text)

    if ($null -eq $Text) {
        return ''
    }

    return [System.Security.SecurityElement]::Escape($Text)
}

function Build-SheetXml {
    param([object[]]$Records)

    $rowsXml = New-Object System.Collections.Generic.List[string]

    $headerCells = for ($i = 0; $i -lt $standardHeaders.Count; $i++) {
        $col = [char](65 + $i)
        "<c r='${col}1' t='inlineStr'><is><t>$(Escape-XmlText $standardHeaders[$i])</t></is></c>"
    }
    $rowsXml.Add("<row r='1'>" + ($headerCells -join '') + '</row>')

    for ($rowIndex = 0; $rowIndex -lt $Records.Count; $rowIndex++) {
        $sheetRow = $rowIndex + 2
        $record = $Records[$rowIndex]
        $cells = New-Object System.Collections.Generic.List[string]

        foreach ($colIndex in 0..11) {
            $col = [char](65 + $colIndex)
            switch ($colIndex) {
                0 { $value = $record.题型 }
                1 { $value = $record.题干 }
                2 { $value = $record.选项A }
                3 { $value = $record.选项B }
                4 { $value = $record.选项C }
                5 { $value = $record.选项D }
                6 { $value = $record.选项E }
                7 { $value = $record.选项F }
                8 { $value = $record.正确答案 }
                9 { $value = $record.分值 }
                10 { $value = $record.来源题库 }
                11 { $value = $record.题目难度 }
            }

            if ($null -eq $value -or $value -eq '') {
                continue
            }

            if ($colIndex -eq 9) {
                $cells.Add("<c r='${col}${sheetRow}'><v>$value</v></c>")
            }
            else {
                $preserve = if ($value -match '^\s' -or $value -match '\s$') { " xml:space='preserve'" } else { '' }
                $escaped = Escape-XmlText ([string]$value)
                $cells.Add("<c r='${col}${sheetRow}' t='inlineStr'><is><t$preserve>$escaped</t></is></c>")
            }
        }

        $rowsXml.Add("<row r='$sheetRow'>" + ($cells -join '') + '</row>')
    }

    $lastRow = [Math]::Max(1, $Records.Count + 1)
    $dimension = "A1:L$lastRow"

    return @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="$dimension"/>
  <sheetViews>
    <sheetView workbookViewId="0"/>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <sheetData>
    $($rowsXml -join "`n    ")
  </sheetData>
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>
"@
}

if (-not (Test-Path $sourcePath)) {
    throw "未找到源文件: $sourcePath"
}

if (-not (Test-Path $templatePath)) {
    throw "未找到模板文件: $templatePath"
}

$sourceRows = Read-FirstWorksheetRows -Path $sourcePath
$records = New-Object System.Collections.Generic.List[object]

foreach ($row in ($sourceRows | Select-Object -Skip 1)) {
    $cells = $row.Cells
    $sourceType = [string]$cells['A']

    if ([string]::IsNullOrWhiteSpace($sourceType) -or $sourceType -eq '试题类型') {
        continue
    }

    $questionType = $typeMapping[$sourceType]
    if (-not $questionType) {
        throw "发现未映射题型: $sourceType"
    }

    $answer = Normalize-Answer -QuestionType $questionType -Answer ([string]$cells['E'])

    $optionA = [string]$cells['F']
    $optionB = [string]$cells['G']
    $optionC = [string]$cells['H']
    $optionD = [string]$cells['I']
    $optionE = [string]$cells['J']
    $optionF = [string]$cells['K']

    if ($questionType -eq '判断') {
        $optionA = '正确'
        $optionB = '错误'
        $optionC = ''
        $optionD = ''
        $optionE = ''
        $optionF = ''
    }

    $records.Add([pscustomobject]@{
        题型 = $questionType
        题干 = [string]$cells['B']
        选项A = $optionA
        选项B = $optionB
        选项C = $optionC
        选项D = $optionD
        选项E = $optionE
        选项F = $optionF
        正确答案 = $answer
        分值 = 1
        来源题库 = [string]$cells['C']
        题目难度 = [string]$cells['D']
    })
}

$sheetXml = Build-SheetXml -Records $records

if (Test-Path $outputPath) {
    Remove-Item -LiteralPath $outputPath
}

$templateZip = [System.IO.Compression.ZipFile]::OpenRead($templatePath)
try {
    $outputStream = [System.IO.File]::Open($outputPath, [System.IO.FileMode]::CreateNew)
    try {
        $outputZip = New-Object System.IO.Compression.ZipArchive($outputStream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
        try {
            foreach ($entry in $templateZip.Entries) {
                if ($entry.FullName -eq 'xl/worksheets/sheet1.xml') {
                    continue
                }

                $newEntry = $outputZip.CreateEntry($entry.FullName, [System.IO.Compression.CompressionLevel]::Optimal)
                $inStream = $entry.Open()
                $outStream = $newEntry.Open()
                try {
                    $inStream.CopyTo($outStream)
                }
                finally {
                    $outStream.Dispose()
                    $inStream.Dispose()
                }
            }

            $sheetEntry = $outputZip.CreateEntry('xl/worksheets/sheet1.xml', [System.IO.Compression.CompressionLevel]::Optimal)
            $writer = New-Object System.IO.StreamWriter($sheetEntry.Open(), [System.Text.UTF8Encoding]::new($false))
            try {
                $writer.Write($sheetXml)
            }
            finally {
                $writer.Dispose()
            }
        }
        finally {
            $outputZip.Dispose()
        }
    }
    finally {
        $outputStream.Dispose()
    }
}
finally {
    $templateZip.Dispose()
}

$groupedSummary = $records | Group-Object 题型 | Sort-Object Name
Write-Output "标准化完成: $outputPath"
Write-Output ("题目总数: " + $records.Count)
foreach ($group in $groupedSummary) {
    Write-Output ("题型统计: {0}={1}" -f $group.Name, $group.Count)
}