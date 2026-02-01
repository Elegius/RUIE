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
WizardImageFile=compiler:wizmodernimage-is.bmp
WizardSmallImageFile=compiler:wizmodernsmallimage-is.bmp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIconTask}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIconTask}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1
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
Name: "{group}\{cm:UninstallProgram,RUIE}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\RUIE"; Filename: "{app}\RUIE.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon; Comment: "RSI Launcher UI Editor"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\RUIE"; Filename: "{app}\RUIE.exe"; IconFilename: "{app}\icon.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\RUIE.exe"; Description: "{cm:LaunchProgram,RUIE}"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: dirifempty; Name: "{app}"
Type: dirifempty; Name: "{autopf}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  Msg: String;
begin
  if CurStep = ssFinished then
  begin
    Msg := 'RUIE has been successfully installed!' + #13#10 + #13#10 +
           'Important: This application requires Administrator privileges to modify the RSI Launcher.' + #13#10 + #13#10 +
           'When you run RUIE, you may receive a UAC (User Account Control) prompt. Click "Yes" to proceed.' + #13#10 + #13#10 +
           'For more information, visit: https://github.com/Elegius/RUIE';
    MsgBox(Msg, mbInformation, MB_OK);
  end;
end;

procedure InitializeWizard();
var
  Msg: String;
begin
  Msg := 'RUIE - RSI Launcher UI Editor' + #13#10 + #13#10 +
         'Version: 0.2 Alpha' + #13#10 + #13#10 +
         'This installer will set up RUIE on your system.' + #13#10 + #13#10 +
         'IMPORTANT DISCLAIMER:' + #13#10 +
         '- RUIE is a fan-made project NOT affiliated with Cloud Imperium Games' + #13#10 +
         '- Star Citizen and RSI Launcher are trademarks of Cloud Imperium Games' + #13#10 +
         '- Use this tool at your own risk and in accordance with CIG Terms of Service';
  MsgBox(Msg, mbInformation, MB_OK);
end;
