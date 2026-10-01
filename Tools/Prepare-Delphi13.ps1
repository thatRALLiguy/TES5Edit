# Run after git submodule update --init --recursive, before opening Delphi.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$dependencies = @(
    @{ Name = 'SynEdit'; Revision = '2e3ff22c6c01a554707faa9defc50dbd16e15923'; Patch = 'synedit-delphi13.patch' },
    @{ Name = 'jvcl'; Revision = 'dba248a275c2286699f357ddc94c9c0cfa888174'; Patch = 'jvcl-delphi13.patch' },
    @{ Name = 'jcl'; Revision = 'e1de11e6e204006d64257164260952424a76814f'; Patch = 'jcl-delphi13.patch' },
    @{ Name = 'VirtualTrees'; Revision = '413663793628a726cae932f8ed2935b1a0a9cfdc'; Patch = 'virtualtrees-delphi13.patch' },
    @{ Name = 'vcl-styles-utils'; Revision = '8a73bb0c56169ed1185f92f473884227f246b6db'; Patch = 'vcl-styles-utils-delphi13.patch' },
    @{ Name = 'ImagingLib'; Revision = '953f27413dc7e994b2ca07d05712458b2b87d19e'; Patch = 'imaginglib-delphi13.patch' },
    @{ Name = 'lz4-delphi'; Revision = '6d6244eb768797c1a5aa6346848e6ee68d096e0f'; Patch = 'lz4-delphi-delphi13.patch' },
    @{ Name = 'libdeflate-pas'; Revision = 'c044fe1a7b0e2e9930c6a5110c7bd194a4872c91'; Patch = 'libdeflate-pas-delphi13.patch' }
)

foreach ($dependency in $dependencies) {
    $dependencyRoot = Join-Path $repoRoot ('External\' + $dependency.Name)
    $patchPath = Join-Path $PSScriptRoot ('compatibility\' + $dependency.Patch)
    $actualRevision = & git -C $dependencyRoot rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actualRevision -ne $dependency.Revision) {
        throw "$($dependency.Name) revision differs from the reviewed dependency. Review the compatibility patch before proceeding."
    }

    # A failed reverse check is expected on an unpatched checkout. PowerShell
    # 5 treats redirected native stderr as an error, so allow it for this probe.
    $ErrorActionPreference = 'Continue'
    & git -C $dependencyRoot apply --reverse --check $patchPath 2>&1 | Out-Null
    $alreadyApplied = $LASTEXITCODE -eq 0
    $ErrorActionPreference = 'Stop'
    if ($alreadyApplied) {
        Write-Output "$($dependency.Name) Delphi 13 compatibility patch is already applied."
    } else {
        & git -C $dependencyRoot apply --check $patchPath
        if ($LASTEXITCODE -ne 0) { throw "$($dependency.Name) patch does not apply cleanly." }
        & git -C $dependencyRoot apply $patchPath
        if ($LASTEXITCODE -ne 0) { throw "$($dependency.Name) patch failed." }
        Write-Output "Applied $($dependency.Name) Delphi 13 compatibility patch."
    }
}

$jclInclude = Join-Path $repoRoot 'External\jcl\jcl\source\include'
foreach ($configName in @('jcld29win32.inc', 'jcld29win64.inc')) {
    $configPath = Join-Path $jclInclude $configName
    if (-not (Test-Path -LiteralPath $configPath)) {
        Copy-Item -LiteralPath (Join-Path $jclInclude 'jcl.template.inc') -Destination $configPath
        Write-Output "Created JCL configuration $configName."
    }
}
