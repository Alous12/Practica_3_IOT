param([string]$ArduinoJsonPath = '.pio/libdeps/esp32dev/ArduinoJson/src')
$ErrorActionPreference = 'Stop'
$projectPath = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $projectPath
try {
    $jsonPath = $ArduinoJsonPath
    if (-not (Test-Path "$jsonPath/ArduinoJson.h")) {
        throw 'Primero ejecutar: pio run -e esp32dev'
    }
    $commonArgs = @('-std=c++17', '-Wall', '-Wextra', '-I', 'test/luciana/stubs',
                    '-I', 'src', '-I', 'include', '-I', $jsonPath)
    $hardwareSources = @('src/sensors/PirSensor.cpp', 'src/actuators/DoorLock.cpp')
    $tests = @(
        @{ Source = 'test/luciana/test_firmware.cpp'; Extra = @('src/app/SmartObject.cpp') },
        @{ Source = 'test/ruben/test_hardware.cpp'; Extra = @() },
        @{ Source = 'test/luciana/test_edge.cpp'; Extra = @('src/app/SmartObject.cpp', 'src/rules/AutoLockRule.cpp') },
        @{ Source = 'test/luciana/test_alarm.cpp'; Includes = @('-I', 'test/luciana/alarm_stubs');
           Extra = @('src/app/SmartObject.cpp', 'src/settings/OperatingMode.cpp',
                     'src/rules/AutoLockRule.cpp', 'src/rules/AlarmRule.cpp') }
    )
    foreach ($case in $tests) {
        $binaryPath = [IO.Path]::ChangeExtension($case.Source, '.exe')
        & g++ @($case.Includes) @commonArgs $case.Source @hardwareSources @($case.Extra) -o $binaryPath
        if ($LASTEXITCODE -ne 0) { throw "No compilo $($case.Source)" }
        & (Join-Path $projectPath $binaryPath)
        if ($LASTEXITCODE -ne 0) { throw "Fallo $($case.Source)" }
    }
} finally {
    Pop-Location
}
