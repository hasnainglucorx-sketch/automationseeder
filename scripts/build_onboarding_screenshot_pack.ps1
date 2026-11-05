$ErrorActionPreference = 'Stop'

$workspace = Split-Path -Parent $PSScriptRoot
$destinationRoot = Join-Path $workspace 'output\PRT-0392-onboarding-screens-2026-10-16'
$iosSource = 'C:\Users\Hasnain\Downloads\IOS NEW FLow App 1 oct 2026'
$androidSource = 'C:\Users\Hasnain\Downloads\Android'

$iosDestination = Join-Path $destinationRoot 'ios-22-step-build'
$androidDestination = Join-Path $destinationRoot 'android-12-step-build'
$errorDestination = Join-Path $destinationRoot 'errors-and-blocking'

New-Item -ItemType Directory -Force -Path $iosDestination, $androidDestination, $errorDestination | Out-Null

$manifest = [System.Collections.Generic.List[object]]::new()

function Copy-Evidence {
    param(
        [Parameter(Mandatory)] [string] $Platform,
        [Parameter(Mandatory)] [string] $SourceDirectory,
        [Parameter(Mandatory)] [string] $SourceName,
        [Parameter(Mandatory)] [string] $DestinationDirectory,
        [Parameter(Mandatory)] [string] $DestinationName,
        [Parameter(Mandatory)] [string] $Description
    )

    $sourcePath = Join-Path $SourceDirectory $SourceName
    $destinationPath = Join-Path $DestinationDirectory $DestinationName
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Missing source evidence: $sourcePath"
    }
    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    $sourceItem = Get-Item -LiteralPath $sourcePath
    $manifest.Add([pscustomobject]@{
        platform = $Platform
        destination_file = $DestinationName
        description = $Description
        original_file = $SourceName
        original_captured = $sourceItem.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
        sha256 = (Get-FileHash -LiteralPath $destinationPath -Algorithm SHA256).Hash.ToLowerInvariant()
    })
}

$ios = @(
    @('IMG_6429.PNG', 'step-01-your-setup-ios.png', 'Your setup, initial view'),
    @('IMG_6430.PNG', 'step-01-your-setup-expanded-ios.png', 'Your setup, full four-stage list'),
    @('IMG_6431.PNG', 'step-02-before-you-begin-ios.png', 'Before you begin'),
    @('IMG_6432.PNG', 'step-03-tell-us-about-you-ios.png', 'Tell us about you, upper form'),
    @('IMG_6433.PNG', 'step-03-tell-us-about-you-full-ios.png', 'Tell us about you, full saved profile'),
    @('IMG_6434.PNG', 'step-04-application-site-upper-arm-ios.png', 'Application site, back of upper arm selected'),
    @('IMG_6435.PNG', 'step-04-application-site-abdomen-ios.png', 'Application site, abdomen selected'),
    @('IMG_6436.PNG', 'step-05-permissions-overview-ios.png', 'Permissions overview, initial view'),
    @('IMG_6437.PNG', 'step-05-permissions-overview-full-ios.png', 'Permissions overview, full list including critical alerts'),
    @('IMG_6438.PNG', 'step-06-apple-health-intro-ios.png', 'Connect Apple Health introduction'),
    @('IMG_6439.PNG', 'step-06-apple-health-system-popup-off-ios.png', 'Apple Health access sheet with data toggles off'),
    @('IMG_6440.PNG', 'step-06-apple-health-system-popup-on-ios.png', 'Apple Health access sheet with data toggles on'),
    @('IMG_6441.PNG', 'step-07-bluetooth-first-screen-ios.png', 'Allow Bluetooth introduction'),
    @('IMG_6442.PNG', 'step-07-bluetooth-system-popup-ios.png', 'Bluetooth system permission popup'),
    @('IMG_6443.PNG', 'step-08-notifications-first-screen-ios.png', 'Allow notifications introduction'),
    @('IMG_6444.PNG', 'step-08-notifications-system-popup-ios.png', 'Notifications system permission popup'),
    @('IMG_6445.PNG', 'step-09-critical-alerts-first-screen-ios.png', 'Allow critical alerts introduction'),
    @('IMG_6446.PNG', 'step-09-critical-alerts-system-popup-ios.png', 'Critical Alerts system permission popup'),
    @('IMG_6447.PNG', 'step-10-do-not-disturb-guidance-ios.png', 'Breaking through Do Not Disturb guidance'),
    @('IMG_6448.PNG', 'step-11-permission-summary-check-settings-ios.png', 'Permission summary with Do Not Disturb unresolved'),
    @('IMG_6449.PNG', 'step-11-permission-summary-alternate-ios.png', 'Permission summary alternate capture'),
    @('IMG_6450.PNG', 'step-12-low-glucose-70-ios.png', 'Low Glucose Alert at 70 mg/dL with visible validation helper'),
    @('IMG_6451.PNG', 'step-12-low-glucose-83-ios.png', 'Low Glucose Alert at 83 mg/dL with visible validation helper'),
    @('IMG_6452.PNG', 'step-13-high-glucose-141-ios.png', 'High Glucose Alert at 141 mg/dL with visible validation helper'),
    @('IMG_6453.PNG', 'step-13-high-glucose-142-ios.png', 'High Glucose Alert at 142 mg/dL with visible validation helper'),
    @('IMG_6454.PNG', 'step-14-scan-your-sensor-ios.png', 'Scan your sensor introduction'),
    @('IMG_6455.PNG', 'step-14-camera-system-popup-ios.png', 'Camera system permission popup'),
    @('IMG_6456.PNG', 'step-14-camera-after-allow-ios.png', 'Live camera scanner after allowing access'),
    @('IMG_6457.PNG', 'step-14-manual-sensor-id-ios.png', 'Manual Sensor ID entry'),
    @('IMG_6458.PNG', 'step-14-confirm-sensor-id-ios.png', 'Confirm Sensor ID warning'),
    @('IMG_6459.PNG', 'step-15-sensor-registered-ios.png', 'Sensor registered'),
    @('IMG_6460.PNG', 'step-16-clean-and-dry-skin-ios.png', 'Clean and dry your skin'),
    @('IMG_6461.PNG', 'step-17-take-out-sensor-ios.png', 'Take out your sensor'),
    @('IMG_6462.PNG', 'step-18-remove-cap-ios.png', 'Remove the cap'),
    @('IMG_6463.PNG', 'step-19-place-applicator-ios.png', 'Place the applicator'),
    @('IMG_6464.PNG', 'step-20-press-and-hold-voice-on-ios.png', 'Press and hold, voice guide on'),
    @('IMG_6465.PNG', 'step-20-press-and-hold-voice-off-ios.png', 'Press and hold, voice guide off'),
    @('IMG_6466.PNG', 'step-20-ten-seconds-complete-ios.png', 'Ten seconds complete'),
    @('IMG_6467.PNG', 'step-21-remove-applicator-ios.png', 'Remove the applicator'),
    @('IMG_6468.PNG', 'step-22-sensor-secure-ios.png', 'Make sure your sensor is secure'),
    @('IMG_6469.PNG', 'poststep-transmitter-discovery-ios.png', 'Transmitter discovery'),
    @('IMG_6470.PNG', 'poststep-transmitter-qr-scanner-ios.png', 'Transmitter QR scanner'),
    @('IMG_6471.PNG', 'poststep-transmitter-selection-ios.png', 'Transmitter selection confirmation'),
    @('IMG_6472.PNG', 'poststep-transmitter-pairing-recovery-ios.png', 'Connecting plus no-transmitters-found recovery state'),
    @('IMG_6473.PNG', 'poststep-sensor-warm-up-ios.png', 'Sensor warm-up')
)

foreach ($entry in $ios) {
    Copy-Evidence -Platform 'iOS' -SourceDirectory $iosSource -SourceName $entry[0] -DestinationDirectory $iosDestination -DestinationName $entry[1] -Description $entry[2]
}

$android = @(
    @('Screenshot_20260728_171406_CGMx 1.jpg', 'prestep-profile-form-partial-dark-android.jpg', 'Tell us about you, partial form, dark theme'),
    @('Screenshot_20260728_171411_CGMx 1.jpg', 'prestep-profile-form-full-dark-android.jpg', 'Tell us about you, full form, dark theme'),
    @('Screenshot_20260728_171423_CGMx 1.jpg', 'prestep-profile-form-partial-light-android.jpg', 'Tell us about you, partial form, light theme'),
    @('Screenshot_20260728_171425_CGMx 1.jpg', 'prestep-profile-form-full-light-android.jpg', 'Tell us about you, full form, light theme'),
    @('Screenshot_20260728_171511_CGMx 1.jpg', 'step-01-bluetooth-first-screen-light-android.jpg', 'Allow Bluetooth introduction, light theme'),
    @('Screenshot_20260728_171519_CGMx 1.jpg', 'step-01-bluetooth-first-screen-dark-android.jpg', 'Allow Bluetooth introduction, dark theme'),
    @('Screenshot_20260728_171523_Permission controller.jpg', 'step-01-bluetooth-system-popup-dark-android.jpg', 'Nearby devices system popup, dark theme'),
    @('Screenshot_20260728_171532_Permission controller.jpg', 'step-01-bluetooth-system-popup-light-android.jpg', 'Nearby devices system popup, light theme'),
    @('Screenshot_20260728_171537_CGMx 1.jpg', 'step-02-notifications-first-screen-light-android.jpg', 'Allow notifications introduction, light theme'),
    @('Screenshot_20260728_171543_CGMx 1.jpg', 'step-02-notifications-first-screen-dark-android.jpg', 'Allow notifications introduction, dark theme'),
    @('Screenshot_20260728_171547_Permission controller.jpg', 'step-02-notifications-system-popup-android.jpg', 'Notifications system popup'),
    @('Screenshot_20260728_171551_CGMx 1.jpg', 'step-03-dnd-first-screen-dark-android.jpg', 'Override Do Not Disturb introduction, dark theme'),
    @('Screenshot_20260728_171602_CGMx 1.jpg', 'step-03-dnd-first-screen-light-android.jpg', 'Override Do Not Disturb introduction, light theme'),
    @('Screenshot_20260728_171610_Settings.jpg', 'step-03-dnd-settings-before-allow-android.jpg', 'Do not disturb permission settings before grant'),
    @('Screenshot_20260728_171614_Settings.jpg', 'step-03-dnd-system-popup-android.jpg', 'Do Not Disturb special-access confirmation popup'),
    @('Screenshot_20260728_171617_Settings.jpg', 'step-03-dnd-settings-after-allow-android.jpg', 'Do not disturb permission settings after grant'),
    @('Screenshot_20260728_171628_CGMx 1.jpg', 'step-04-permission-summary-light-android.jpg', 'Permission summary, light theme'),
    @('Screenshot_20260728_171637_CGMx 1.jpg', 'step-04-permission-summary-dark-android.jpg', 'Permission summary, dark theme'),
    @('Screenshot_20260728_171648_CGMx 1.jpg', 'step-05-low-glucose-default-dark-android.jpg', 'Low Glucose Alert default 3.9 mmol/L, dark theme'),
    @('Screenshot_20260728_171654_CGMx 1.jpg', 'step-05-low-glucose-default-light-android.jpg', 'Low Glucose Alert default 3.9 mmol/L, light theme'),
    @('Screenshot_20260728_171658_CGMx 1.jpg', 'step-06-high-glucose-default-light-android.jpg', 'High Glucose Alert default 10.0 mmol/L, light theme'),
    @('Screenshot_20260728_171705_CGMx 1.jpg', 'step-06-high-glucose-default-dark-android.jpg', 'High Glucose Alert default 10.0 mmol/L, dark theme'),
    @('Screenshot_20260728_171709_CGMx 1.jpg', 'step-07-instructional-video-dark-android.jpg', 'How to apply your sensor video, dark theme'),
    @('Screenshot_20260728_171717_CGMx 1.jpg', 'step-07-instructional-video-light-android.jpg', 'How to apply your sensor video, light theme'),
    @('Screenshot_20260728_171719_CGMx 1.jpg', 'step-08-scan-your-sensor-light-android.jpg', 'Scan your sensor, light theme'),
    @('Screenshot_20260728_171726_CGMx 1.jpg', 'step-08-scan-your-sensor-dark-android.jpg', 'Scan your sensor, dark theme'),
    @('Screenshot_20260728_171736_CGMx 1.jpg', 'step-08-scan-your-sensor-alternate-android.jpg', 'Scan your sensor alternate light capture'),
    @('Screenshot_20260728_171742_Permission controller.jpg', 'step-08-camera-system-popup-android.jpg', 'Camera system permission popup and app recovery message'),
    @('Screenshot_20260728_171750_CGMx 1.jpg', 'step-08-camera-after-allow-light-android.jpg', 'Live camera scanner after allowing access, light theme'),
    @('Screenshot_20260728_171802_CGMx 1.jpg', 'step-08-camera-after-allow-dark-android.jpg', 'Live camera scanner after allowing access, dark theme'),
    @('Screenshot_20260728_171814_CGMx 1.jpg', 'step-08-manual-sensor-id-empty-dark-android.jpg', 'Manual Sensor ID entry empty, dark theme'),
    @('Screenshot_20260728_171821_CGMx 1.jpg', 'step-08-manual-sensor-id-empty-light-android.jpg', 'Manual Sensor ID entry empty, light theme'),
    @('Screenshot_20260728_171829_CGMx 1.jpg', 'step-08-manual-sensor-id-entered-light-android.jpg', 'Manual Sensor ID entry populated, light theme'),
    @('Screenshot_20260728_171835_CGMx 1.jpg', 'step-08-manual-sensor-id-entered-dark-android.jpg', 'Manual Sensor ID entry populated, dark theme'),
    @('Screenshot_20260728_171844_CGMx 1.jpg', 'step-09-remove-sensor-from-box-dark-android.jpg', 'Remove the sensor from the box, dark theme'),
    @('Screenshot_20260728_171850_CGMx 1.jpg', 'step-09-remove-sensor-from-box-light-android.jpg', 'Remove the sensor from the box, light theme'),
    @('Screenshot_20260728_171853_CGMx 1.jpg', 'step-10-application-site-upper-arm-light-android.jpg', 'Application site, back of upper arm selected, light theme'),
    @('Screenshot_20260728_171856_CGMx 1.jpg', 'step-10-application-site-upper-arm-light-alt-android.jpg', 'Application site alternate light capture'),
    @('Screenshot_20260728_171904_CGMx 1.jpg', 'step-10-application-site-upper-arm-dark-android.jpg', 'Application site, back of upper arm selected, dark theme'),
    @('Screenshot_20260728_171906_CGMx 1.jpg', 'step-10-application-site-upper-arm-dark-alt-android.jpg', 'Application site alternate dark capture'),
    @('Screenshot_20260728_171911_CGMx 1.jpg', 'step-11-unscrew-applicator-cap-dark-android.jpg', 'Unscrew the applicator cap, dark theme'),
    @('Screenshot_20260728_171917_CGMx 1.jpg', 'step-11-unscrew-applicator-cap-light-android.jpg', 'Unscrew the applicator cap, light theme'),
    @('Screenshot_20260728_171919_CGMx 1.jpg', 'step-12-attach-transmitter-light-android.jpg', 'Attach the transmitter, light theme'),
    @('Screenshot_20260728_171925_CGMx 1.jpg', 'step-12-attach-transmitter-dark-android.jpg', 'Attach the transmitter, dark theme'),
    @('Screenshot_20260728_171930_CGMx 1.jpg', 'poststep-transmitter-discovery-dark-android.jpg', 'Transmitter discovery, dark theme'),
    @('Screenshot_20260728_171937_CGMx 1.jpg', 'poststep-transmitter-discovery-light-android.jpg', 'Transmitter discovery, light theme'),
    @('Screenshot_20260728_171943_CGMx 1.jpg', 'poststep-transmitter-discovery-list-light-android.jpg', 'Transmitter discovery list and supporting actions, light theme'),
    @('Screenshot_20260728_171949_CGMx 1.jpg', 'poststep-transmitter-discovery-list-dark-android.jpg', 'Transmitter discovery list and supporting actions, dark theme'),
    @('Screenshot_20260728_171952_CGMx 1.jpg', 'poststep-transmitter-recovery-dark-android.jpg', 'Transmitter recovery and alternate actions, dark theme'),
    @('Screenshot_20260728_171958_CGMx 1.jpg', 'poststep-transmitter-manual-entry-dark-android.jpg', 'Manual transmitter entry, dark theme'),
    @('Screenshot_20260728_172007_CGMx 1.jpg', 'poststep-transmitter-manual-entry-light-android.jpg', 'Manual transmitter entry, light theme'),
    @('Screenshot_20260824_172803_CGMx 1.jpg', 'poststep-transmitter-pairing-android.jpg', 'Transmitter pairing/connecting state'),
    @('Screenshot_20260824_172820_CGMx 1.jpg', 'poststep-sensor-warm-up-light-android.jpg', 'Sensor warm-up, light theme'),
    @('Screenshot_20260824_172830_CGMx 1.jpg', 'poststep-sensor-warm-up-dark-android.jpg', 'Sensor warm-up, dark theme')
)

foreach ($entry in $android) {
    Copy-Evidence -Platform 'Android' -SourceDirectory $androidSource -SourceName $entry[0] -DestinationDirectory $androidDestination -DestinationName $entry[1] -Description $entry[2]
}

Copy-Evidence -Platform 'iOS' -SourceDirectory $iosSource -SourceName 'IMG_6472.PNG' -DestinationDirectory $errorDestination -DestinationName 'no-transmitters-found-ios.png' -Description 'No transmitters found recovery state'
Copy-Evidence -Platform 'Android' -SourceDirectory $androidSource -SourceName 'Screenshot_20260728_171742_Permission controller.jpg' -DestinationDirectory $errorDestination -DestinationName 'camera-permission-required-android.jpg' -Description 'Camera required recovery plus system permission popup'
Copy-Evidence -Platform 'Android' -SourceDirectory $androidSource -SourceName 'Screenshot_20260824_172838_CGMx 1.jpg' -DestinationDirectory $errorDestination -DestinationName 'session-interrupted-android.jpg' -Description 'Session has been interrupted blocking modal'

$manifestPath = Join-Path $destinationRoot 'manifest.csv'
$manifest | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8

$zipPath = Join-Path $workspace 'output\PRT-0392-onboarding-screens-2026-10-16.zip'
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -LiteralPath $destinationRoot -DestinationPath $zipPath -CompressionLevel Optimal

Write-Output $destinationRoot
Write-Output $zipPath
