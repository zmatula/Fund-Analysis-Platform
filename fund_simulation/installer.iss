; Inno Setup Script for Monte Carlo Fund Simulation
; Requires Inno Setup 6.0 or higher: https://jrsoftware.org/isinfo.php

#define MyAppName "Monte Carlo Fund Simulation"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company Name"
#define MyAppURL "https://yourcompany.com"
#define MyAppExeName "launch_fund_simulation.bat"

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
OutputBaseFilename=FundSimulation_Setup_v{#MyAppVersion}
;SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Application files
Source: "app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "launch_fund_simulation.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "fund_simulation\*"; DestDir: "{app}\fund_simulation"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "USER_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
; Icon (if exists)
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  PythonInstalled: Boolean;
begin
  Result := True;

  // Check if Python is installed
  PythonInstalled := False;

  if Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
      PythonInstalled := True;
  end;

  if not PythonInstalled then
  begin
    if MsgBox('Python 3.8 or higher is required but was not detected.' + #13#10 + #13#10 +
              'Would you like to download Python now?' + #13#10 + #13#10 +
              'Click Yes to open Python download page,' + #13#10 +
              'or No to cancel installation.',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOW, ewNoWait, ResultCode);
      Result := False;
    end
    else
      Result := False;
  end;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nREQUIREMENTS:%n• Python 3.8 or higher%n• Internet connection (for first-time setup)%n%nIt is recommended that you close all other applications before continuing.
