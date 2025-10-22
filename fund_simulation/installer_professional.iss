; Professional Inno Setup Script for Monte Carlo Fund Simulation
; Creates a standalone Windows installer with NO Python dependency
; Requires Inno Setup 6.0 or higher: https://jrsoftware.org/isinfo.php

#define MyAppName "Monte Carlo Fund Simulation"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company Name"
#define MyAppURL "https://yourcompany.com"
#define MyAppExeName "MonteCarloFundSimulation.exe"

[Setup]
; App identity
AppId={{B8F9E5D3-7A2C-4F1B-9E6D-8C3A5B7D9F2E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Output configuration
OutputDir=installer_output
OutputBaseFilename=MonteCarloFundSimulation_Setup_v{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMADictionarySize=1048576
LZMANumFastBytes=273

; Visual style
WizardStyle=modern
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Versioning
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCopyright=Copyright (C) 2025 {#MyAppPublisher}

; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main executable (built by PyInstaller)
Source: "dist\MonteCarloFundSimulation.exe"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "USER_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Visual C++ Redistributables (if needed)
; Uncomment if your app requires VC++ runtime
; Source: "vcredist_x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\User Guide"; Filename: "{app}\USER_GUIDE.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Optional: Install VC++ Redistributables
; Filename: "{tmp}\vcredist_x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Visual C++ Runtime..."; Flags: waituntilterminated skipifdoesntexist

; Launch application after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
var
  ProgressPage: TOutputProgressWizardPage;

procedure InitializeWizard();
begin
  // Create custom progress page
  ProgressPage := CreateOutputProgressPage('Preparing Installation', 'Please wait while Setup prepares to install {#MyAppName} on your computer.');
end;

function InitializeSetup(): Boolean;
begin
  // No Python check needed - we're fully standalone!
  Result := True;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThis is a STANDALONE application:%n• NO Python required%n• NO dependencies to install%n• Ready to run immediately after installation%n%nIt is recommended that you close all other applications before continuing.
ReadyLabel2a=Setup is now ready to begin installing [name] on your computer.%n%nThe application is fully self-contained and ready to use.
FinishedLabel=Setup has finished installing [name] on your computer.%n%nThe application can be launched by selecting the installed icons.

[UninstallDelete]
Type: filesandordirs; Name: "{app}\temp_*"
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"
