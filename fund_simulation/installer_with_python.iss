; Inno Setup Script for Monte Carlo Fund Simulation
; WITH EMBEDDED PYTHON - No Python installation required!
; Requires Inno Setup 6.0 or higher: https://jrsoftware.org/isinfo.php

#define MyAppName "Monte Carlo Fund Simulation"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company Name"
#define MyAppURL "https://yourcompany.com"
#define MyAppExeName "launch_with_embedded_python.bat"

[Setup]
; NOTE: The value of AppId uniquely identifies this application
AppId={{B8F9E5D3-7A2C-4F1B-9E6D-8C3A5B7D9F2E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=FundSimulation_WithPython_Setup_v{#MyAppVersion}
;SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
LZMAUseSeparateProcess=yes
LZMADictionarySize=1048576

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone

[Files]
; Application files
Source: "app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "launch_with_embedded_python.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "fund_simulation\*"; DestDir: "{app}\fund_simulation"; Flags: ignoreversion recursesubdirs createallsubdirs

; Embedded Python (the key addition!)
Source: "python_embedded\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme skipifsourcedoesntexist
Source: "USER_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Icon (if exists)
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThis version includes:%n• Embedded Python (no installation needed!)%n• All dependencies%n• Complete standalone application%n%nNo other software required!%n%nIt is recommended that you close all other applications before continuing.
FinishedLabel=Setup has finished installing [name] on your computer.%n%nThe application is completely self-contained and ready to use. Double-click the desktop icon to launch.
