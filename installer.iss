#define MyAppName "IR FLOW"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "Fluxoly"
#define MyAppURL "https://fluxoly.com"
#define MyAppExeName "IR FLOW.exe"

[Setup]
AppId={{7C0D6760-7A3A-4E1C-A1A7-CC4D65D5E2E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\IR Flow
DefaultGroupName=IR FLOW
DisableProgramGroupPage=yes
LicenseFile=
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=installer_output
OutputBaseFilename=IR FLOW Setup
SetupIconFile=assets\ir_flow.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter=IR FLOW.exe
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "release\IR FLOW.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\database.db"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\IR FLOW"; Filename: "{app}\IR FLOW.exe"; IconFilename: "{app}\IR FLOW.exe"
Name: "{autodesktop}\IR FLOW"; Filename: "{app}\IR FLOW.exe"; Tasks: desktopicon; IconFilename: "{app}\IR FLOW.exe"

[Run]
Filename: "{app}\IR FLOW.exe"; Description: "Abrir IR FLOW agora"; Flags: nowait postinstall skipifsilent
