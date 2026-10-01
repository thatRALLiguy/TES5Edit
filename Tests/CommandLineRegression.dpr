program CommandLineRegression;

{$APPTYPE CONSOLE}
{$R+}

uses
  System.SysUtils,
  wbCommandLine in '..\Core\wbCommandLine.pas';

procedure Require(aCondition: Boolean; const aMessage: string);
begin
  if not aCondition then
    raise Exception.Create(aMessage);
end;

var
  Value: string;
  Index: Integer;
begin
  try
    // Run with: "" -probe:value payload ""
    Require(ParamCount = 4, 'Expected four test arguments');
    Require((ParamStr(1) = '') and (ParamStr(2) = '-probe:value') and
      (ParamStr(3) = 'payload') and (ParamStr(4) = ''), 'Unexpected test arguments');
    Require(wbFindCmdLineParam('probe', Value), 'Switch after empty argument not found');
    Require(Value = 'value', 'Incorrect switch value');
    Require(not wbFindCmdLineParam('absent', Value), 'Absent switch found');
    Require(Value = '', 'Absent switch must clear output');
    Index := 1;
    Require(wbFindCmdLineParam(Index, Value), 'Empty positional argument lost');
    Require((Value = '') and (Index = 2), 'Wrong empty positional result');
    Require(wbFindCmdLineParam(Index, Value), 'Nonempty positional argument lost');
    Require((Value = 'payload') and (Index = 4), 'Switch was not skipped');
    Require(wbFindCmdLineParam(Index, Value), 'Trailing empty argument lost');
    Require((Value = '') and (Index = 5), 'Wrong trailing empty result');
    Require(not wbFindCmdLineParam(Index, Value), 'Unexpected extra argument');
    WriteLn('PASS: empty arguments and switch/positional iteration');
  except
    on E: Exception do begin
      WriteLn(ErrOutput, E.ClassName, ': ', E.Message);
      ExitCode := 1;
    end;
  end;
end.
