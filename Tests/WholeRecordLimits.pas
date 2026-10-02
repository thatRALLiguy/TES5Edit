unit WholeRecordLimits;
var Report: TStringList;

procedure Note(S: string);
begin
  Report.Add(S);
  Report.SaveToFile('@AUDIT@whole-results.txt');
  AddMessage(S);
end;

procedure CheckResult(B: Boolean; S: string);
begin
  if B then Note('PASS: ' + S) else Note('FAIL: ' + S);
end;

function ListRecord(N: Integer): IInterface;
begin
  Result := ElementByIndex(GroupBySignature(FileByName('Limits' + IntToStr(N) + '.esm'), 'LVLI'), 0);
end;

procedure Snapshot(F: IInterface; Name: string);
var Stream: TFileStream;
begin
  Stream := TFileStream.Create('@AUDIT@' + Name + '.esm', fmCreate);
  try FileWriteToStream(F, Stream, 0); finally Stream.Free; end;
end;

procedure RejectWhole(N: Integer);
var Target, E: IInterface; Tag: string;
begin
  Tag := 'whole-' + IntToStr(N);
  Target := ListRecord(1);
  Snapshot(GetFile(Target), Tag + '-before');
  E := nil;
  try E := ElementAssign(Target, LowInteger, ListRecord(N), False);
  except on Ex: Exception do Note('REJECTED: ' + Ex.Message); end;
  Snapshot(GetFile(Target), Tag + '-after');
  CheckResult(not Assigned(E), Tag + ' rejects assignment');
  CheckResult(ElementCount(ElementByPath(Target, 'Leveled List Entries')) = 1, Tag + ' preserves entries');
  CheckResult(GetElementEditValues(Target, 'LLCT') = '1', Tag + ' preserves count');
  CheckResult(GetElementEditValues(Target, 'EDID') = 'Limit1', Tag + ' preserves editor ID');
end;

procedure RejectCopy(AsNew: Boolean; Tag: string);
var F, Source, E: IInterface; BeforeCount: Integer;
begin
  Source := ListRecord(256);
  F := AddNewFileName(Tag + '.esp');
  AddRequiredElementMasters(Source, F, False, True);
  BeforeCount := ElementCount(F);
  Snapshot(F, Tag + '-before');
  E := nil;
  try E := wbCopyElementToFile(Source, F, AsNew, True);
  except on Ex: Exception do Note('REJECTED: ' + Ex.Message); end;
  Snapshot(F, Tag + '-after');
  CheckResult(not Assigned(E), Tag + ' rejects copy');
  CheckResult(ElementCount(F) = BeforeCount, Tag + ' leaves no destination group or record');
  Source := ListRecord(255);
  AddRequiredElementMasters(Source, F, False, True);
  E := wbCopyElementToFile(Source, F, AsNew, True);
  CheckResult(Assigned(E), Tag + ' allows valid copy');
  CheckResult(ElementCount(ElementByPath(E, 'Leveled List Entries')) = 255, Tag + ' valid copy retains entries');
  CheckResult(GetElementEditValues(E, 'LLCT') = '255', Tag + ' valid copy count');
  Snapshot(F, Tag + '-valid');
end;

procedure ReferenceOnly;
var Source, Target, Forms, Field, E, Linked: IInterface; N, BeforeCount: Integer; Tag: string;
begin
  Target := ListRecord(254);
  Forms := ElementByPath(ElementByIndex(GroupBySignature(FileByName('Unbounded.esm'), 'FLST'), 0), 'FormIDs');
  for N := 256 to 257 do begin
    Source := ListRecord(N);
    Tag := 'reference-' + IntToStr(N);
    Snapshot(GetFile(Source), Tag + '-before');
    AddRequiredElementMasters(Source, GetFile(Target), False, True);
    AddRequiredElementMasters(Source, GetFile(Forms), False, True);
    Field := ElementByPath(ElementByIndex(ElementByPath(Target, 'Leveled List Entries'), 0), 'LVLO\Item');
    if not Assigned(Field) then raise Exception.Create('Missing LVLO Item field');
    E := ElementAssign(Field, LowInteger, Source, False);
    Linked := LinksTo(Field);
    CheckResult(Assigned(Linked) and (GetLoadOrderFormID(Linked) = GetLoadOrderFormID(Source)), Tag + ' nested field assigns only FormID');
    CheckResult(ElementCount(ElementByPath(Target, 'Leveled List Entries')) = 254, Tag + ' nested field retains target count');
    Field := ElementByIndex(Forms, 0);
    E := ElementAssign(Field, LowInteger, Source, False);
    Linked := LinksTo(Field);
    CheckResult(Assigned(Linked) and (GetLoadOrderFormID(Linked) = GetLoadOrderFormID(Source)), Tag + ' subrecord assigns only FormID');
    BeforeCount := ElementCount(Forms);
    E := ElementAssign(Forms, HighInteger, Source, False);
    CheckResult(ElementCount(Forms) = BeforeCount + 1, Tag + ' appends one reference');
    Linked := LinksTo(ElementByIndex(Forms, ElementCount(Forms) - 1));
    CheckResult(Assigned(Linked) and (GetLoadOrderFormID(Linked) = GetLoadOrderFormID(Source)), Tag + ' appended reference resolves');
    CheckResult(ElementCount(ElementByPath(Source, 'Leveled List Entries')) = N, Tag + ' source entries unchanged');
    Snapshot(GetFile(Source), Tag + '-after');
  end;
  Snapshot(GetFile(Target), 'reference-list-valid');
  Snapshot(GetFile(Forms), 'reference-formlist-valid');
end;

procedure Run;
var Target, E: IInterface;
begin
  RejectWhole(256);
  RejectWhole(257);
  RejectCopy(False, 'copy-override');
  RejectCopy(True, 'copy-new');
  Target := ListRecord(1);
  E := ElementAssign(Target, LowInteger, ListRecord(255), False);
  CheckResult(ElementCount(ElementByPath(Target, 'Leveled List Entries')) = 255, 'valid whole-record assignment retains 255 entries');
  CheckResult(GetElementEditValues(Target, 'LLCT') = '255', 'valid whole-record count');
  CheckResult(GetElementEditValues(Target, 'EDID') = 'Limit255', 'valid whole-record editor ID');
  Snapshot(GetFile(Target), 'limits-repaired');
  ReferenceOnly;
  Note('COMPLETE');
end;

function Initialize: Integer;
begin
  Report := TStringList.Create;
  try
    try Run;
    except on E: Exception do Note('HARNESS_ERROR: ' + E.Message); end;
  finally Report.Free; end;
  Result := 0;
end;
end.
