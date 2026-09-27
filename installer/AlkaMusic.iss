; Inno Setup script - builds dist\AlkaMusic-Setup-<version>.exe from the PyInstaller folder dist\AlkaMusic.
; Built by build.ps1 (passes /DAppVersion=...). Per-user install, no admin rights needed.

#define AppName "AlkaMusic"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6B0F3C2E-5A4D-4E8B-9C1F-7A2D8E4B1C35}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Bacilek
AppPublisherURL=https://github.com/Bacilek/AlkaMusic
AppSupportURL=https://github.com/Bacilek/AlkaMusic
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#AppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=AlkaMusic-Setup-{#AppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\AlkaMusic.exe
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
VersionInfoCompany=Bacilek
VersionInfoDescription={#AppName} - instalace

[Languages]
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"

[InstallDelete]
; libraries of the previous version (and the old single-file exe layout)
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\AlkaMusic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\AlkaMusic.exe"
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\AlkaMusic.exe"

[Run]
Filename: "{app}\AlkaMusic.exe"; Description: "Spustit AlkaMusic"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  // A running app (and its yt-dlp/ffmpeg children) would lock the files we want to delete.
  if CurUninstallStep = usUninstall then
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM AlkaMusic.exe', '', SW_HIDE,
      ewWaitUntilTerminated, ResultCode);
end;

[UninstallDelete]
; downloaded tools (yt-dlp, ffmpeg), history and log - the songs on the desktop are kept
Type: filesandordirs; Name: "{localappdata}\AlkaMusic"
Type: filesandordirs; Name: "{app}"
