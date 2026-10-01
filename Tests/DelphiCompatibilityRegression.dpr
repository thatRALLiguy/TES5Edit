program DelphiCompatibilityRegression;

{$APPTYPE CONSOLE}
{$R+}
{$Q+}

uses
  System.Classes,
  System.Contnrs,
  System.SysUtils,
  System.Variants,
  JvInterpreter,
  JvInterpreter_System,
  JvInterpreter_SysUtils,
  JvJCLUtils,
  SynEdit,
  SynEditHighlighter;

procedure Require(Condition: Boolean; const MessageText: string);
begin
  if not Condition then
    raise Exception.Create(MessageText);
end;

procedure CheckScriptSearchRecord;
var
  Script: TJvInterpreterProgram;
  Search: TSearchRec;
  Expected: TDateTime;
  FileName: string;
  FileStream: TFileStream;
  ExpectedLegacy: Integer;
begin
  FileName := ParamStr(0);
  Require(FindFirst(FileName, faAnyFile, Search) = 0, 'Native FindFirst failed');
  try
    Expected := Search.TimeStamp;
  finally
    System.SysUtils.FindClose(Search);
  end;

  FileStream := TFileStream.Create(FileName, fmOpenRead or fmShareDenyNone);
  try
    // FileGetDate uses the same DOS-time conversion as FindFirst on Windows.
    ExpectedLegacy := FileGetDate(FileStream.Handle);
    Require(ExpectedLegacy <> -1, 'Native file date query failed');
  finally
    FileStream.Free;
  end;

  Script := TJvInterpreterProgram.Create(nil);
  try
    // Registered native adapters supply these routines without a source unit.
    Script.Pas.Text :=
      'unit SearchRecordTest; interface implementation' + sLineBreak +
      'function Probe(FileName: string; ExpectedLegacy: Integer): Double;' + sLineBreak +
      'var F: TSearchRec; CopyF: TSearchRec; SavedTime: Integer;' + sLineBreak +
      'begin' + sLineBreak +
      '  if FindFirst(FileName, faAnyFile, F) <> 0 then raise Exception.Create(''FindFirst failed'');' + sLineBreak +
      '  try' + sLineBreak +
      '    SavedTime := F.Time;' + sLineBreak +
      '    if SavedTime <> ExpectedLegacy then raise Exception.Create(''Legacy time format changed'');' + sLineBreak +
      '    CopyF := F;' + sLineBreak +
      '    F.Time := 12345;' + sLineBreak +
      '    if F.Time <> 12345 then raise Exception.Create(''Legacy Time is no longer writable'');' + sLineBreak +
      '    if CopyF.Time <> SavedTime then raise Exception.Create(''Record copy changed'');' + sLineBreak +
      '    if F.TimeStamp <> CopyF.TimeStamp then raise Exception.Create(''Legacy write changed native timestamp'');' + sLineBreak +
      '    Result := F.TimeStamp;' + sLineBreak +
      '  finally FindClose(F); end;' + sLineBreak +
      'end; end.';
    Script.Compile;
    Require(Abs(Double(Script.CallFunction('Probe', nil, [FileName, ExpectedLegacy])) - Expected) < 1E-10,
      'Script TimeStamp differs from the native RTL');
  finally
    Script.Free;
  end;
  WriteLn('PASS: script search, legacy Time read/write, record copy and modern TimeStamp');
end;

procedure CheckTypedListIndexes;
var
  Integers: TIntegerList;
  Marks: TSynEditMarkList;
  Highlighters: TSynHighlighterList;
  Index: NativeInt;
  Mark: TSynEditMark;
  HighlighterClass: TSynCustomHighlighterClass;
begin
  Index := 0;
  Integers := TIntegerList.Create;
  try
    Integers.Add(42);
    Require(Integers[Index] = 42, 'Native-width integer index chose the base pointer property');
    Integers[Index] := 17;
    Require(Integers[0] = 17, 'Integer list write failed');
  finally
    Integers.Free;
  end;
  Marks := TSynEditMarkList.Create(nil);
  try
    Marks.Add(nil);
    Mark := Marks[Index];
    Require(Mark = nil, 'Native-width mark index failed');
    Marks[Index] := nil;
  finally
    Marks.Free;
  end;
  Highlighters := TSynHighlighterList.Create;
  try
    // The list wraps registered highlighters. Only index it when nonempty.
    if Highlighters.Count > 0 then begin
      HighlighterClass := Highlighters[Index];
      Require(HighlighterClass <> nil, 'Native-width highlighter index failed');
    end;
  finally
    Highlighters.Free;
  end;
  WriteLn('PASS: typed list indexes with NativeInt');
end;

begin
  try
    JvInterpreter_System.RegisterJvInterpreterAdapter(GlobalJvInterpreterAdapter);
    JvInterpreter_SysUtils.RegisterJvInterpreterAdapter(GlobalJvInterpreterAdapter);
    CheckScriptSearchRecord;
    CheckTypedListIndexes;
  except
    on E: Exception do begin
      WriteLn(ErrOutput, E.ClassName, ': ', E.Message);
      ExitCode := 1;
    end;
  end;
end.
