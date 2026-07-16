' Launcher robusto — tenta pythonw em varios locais
Set objShell = CreateObject("WScript.Shell")
Set objFSO   = CreateObject("Scripting.FileSystemObject")

scriptDir  = objFSO.GetParentFolderName(WScript.ScriptFullName)
scriptFile = scriptDir & "\Data\locres_csv_importer.py"

' Tentar encontrar pythonw.exe
Dim pythonw
pythonw = ""

On Error Resume Next
Set oExec = objShell.Exec("where pythonw.exe")
If Err.Number = 0 Then
    pythonw = Trim(oExec.StdOut.ReadLine())
End If
On Error GoTo 0

If pythonw = "" Or Not objFSO.FileExists(pythonw) Then
    Dim tries(5)
    tries(0) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe")
    tries(1) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe")
    tries(2) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe")
    tries(3) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe")
    tries(4) = "C:\Python313\pythonw.exe"
    tries(5) = "C:\Python312\pythonw.exe"
    Dim i
    For i = 0 To 5
        If objFSO.FileExists(tries(i)) Then
            pythonw = tries(i)
            Exit For
        End If
    Next
End If

If pythonw = "" Or Not objFSO.FileExists(pythonw) Then
    pythonw = "python"
End If

Dim cmd
cmd = """" & pythonw & """ """ & scriptFile & """"
objShell.Run cmd, 0, False
