' ============================================================
'  Biologiya kursi - serverni to'xtatish
'  Ish stolidagi "Serverni to'xtatish" yorlig'i shu faylni chaqiradi.
'  Jimgina ishlaydi: hech qanday tasdiq oynasi chiqmaydi.
'  Faqat to'xtatib bo'lmagan holatdagina ogohlantiradi.
' ============================================================
Option Explicit

Dim shell, fso, joy, port, url, pidlar, i
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

joy = fso.GetParentFolderName(WScript.ScriptFullName)
port = PortniOqi(joy)
url = "http://127.0.0.1:" & port & "/"

If Not ServerIshlayapti(url) Then
    WScript.Quit 0          ' allaqachon to'xtagan - jimgina chiqamiz
End If

pidlar = TinglayotganPidlar(port)
For i = 0 To UBound(pidlar)
    If pidlar(i) <> "" Then
        shell.Run "taskkill /PID " & pidlar(i) & " /F", 0, True
    End If
Next

WScript.Sleep 700

If ServerIshlayapti(url) Then
    MsgBox "Serverni to'xtatib bo'lmadi." & vbCrLf & vbCrLf & _
           "Vazifalar dispetcherini ochib, python.exe jarayonini yoping.", _
           vbCritical, "Biologiya kursi"
    WScript.Quit 1
End If

WScript.Quit 0


' ------------------------------------------------------------ yordamchilar

Function PortniOqi(papka)
    Dim f
    PortniOqi = "8000"
    If fso.FileExists(papka & "\port.txt") Then
        Set f = fso.OpenTextFile(papka & "\port.txt", 1)
        If Not f.AtEndOfStream Then PortniOqi = Trim(f.ReadLine)
        f.Close
        If Not IsNumeric(PortniOqi) Then PortniOqi = "8000"
    End If
End Function

Function ServerIshlayapti(manzil)
    Dim http
    ServerIshlayapti = False
    On Error Resume Next
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    If Err.Number <> 0 Then
        Err.Clear
        Set http = CreateObject("MSXML2.XMLHTTP")
    End If
    If Err.Number <> 0 Then Exit Function
    http.setTimeouts 1000, 1000, 2000, 2000
    Err.Clear
    http.Open "GET", manzil, False
    http.Send
    If Err.Number = 0 Then ServerIshlayapti = True
    On Error GoTo 0
End Function

Function TinglayotganPidlar(p)
    ' netstat chiqishidan shu portni tinglayotgan jarayon raqamlarini oladi
    Dim exec, matn, qatorlar, q, bolaklar, j, natija, pid
    natija = Array()
    On Error Resume Next
    Set exec = shell.Exec("cmd /c netstat -ano -p TCP")
    If Err.Number <> 0 Then
        TinglayotganPidlar = natija
        Exit Function
    End If
    matn = exec.StdOut.ReadAll()
    On Error GoTo 0

    qatorlar = Split(matn, vbCrLf)
    For Each q In qatorlar
        If InStr(q, ":" & p & " ") > 0 And InStr(UCase(q), "LISTENING") > 0 Then
            bolaklar = Split(q, " ")
            pid = ""
            For j = UBound(bolaklar) To 0 Step -1
                If Trim(bolaklar(j)) <> "" Then
                    pid = Trim(bolaklar(j))
                    Exit For
                End If
            Next
            If IsNumeric(pid) Then
                ReDim Preserve natija(UBound(natija) + 1)
                natija(UBound(natija)) = pid
            End If
        End If
    Next
    TinglayotganPidlar = natija
End Function
