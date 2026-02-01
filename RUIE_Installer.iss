; Inno Setup Script for RUIE (RSI Launcher UI Editor)
; This script creates a professional Windows installer

[Setup]
AppName=RUIE
AppVersion=0.2 Alpha
AppPublisher=RUIE Contributors
AppPublisherURL=https://github.com/Elegius/RUIE
AppSupportURL=https://github.com/Elegius/RUIE/issues
AppUpdatesURL=https://github.com/Elegius/RUIE
DefaultDirName={autopf}\RUIE
DefaultGroupName=RUIE
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=RUIE-0.2-Alpha-Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\RUIE.exe
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=admin
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional Icons"; Flags: unchecked
Name: "associatefiles"; Description: "Associate with theme preset files (.json)"; GroupDescription: "File Association"

[Files]
; Main executable and dependencies
Source: "dist\RUIE\RUIE.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\RUIE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\RUIE"; Filename: "{app}\RUIE.exe"; IconFilename: "{app}\icon.ico"; Comment: "RSI Launcher UI Editor"
Name: "{group}\Uninstall RUIE"; Filename: "{uninstallexe}"
Name: "{autodesktop}\RUIE"; Filename: "{app}\RUIE.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon; Comment: "RSI Launcher UI Editor"

[Run]
Filename: "{app}\RUIE.exe"; Description: "Launch RUIE"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: dirifempty; Name: "{app}"
Type: dirifempty; Name: "{autopf}"
