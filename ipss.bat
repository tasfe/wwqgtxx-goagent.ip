@echo off
setlocal enabledelayedexpansion

rem ����32λ���Ĵ�1�ʹ�0�ַ���
for /l %%i in (1,1,32) do (
set zeroStr=!zeroStr!0
set oneStr=!oneStr!1
)

nslookup -q=TXT _netblocks.google.com 8.8.8.8>result.txt 2>nul
for /f "delims=" %%i in (result.txt) do set "str=%%i"

rem �޳��ַ����е��޹���Ϣ
set "str=%str:"=%"
set "str=%str:*ip4:=%"
set "str=%str:ip4:=%"
set "str=%str:?all=%"

echo.&echo ��������IP�б�������1�������ӣ������ĵȴ�...

(for %%x in (%str%) do (
echo;&echo ;%%x
for /f "delims=./ tokens=1-5" %%i in ("%%x") do (
rem ��ȡÿ���ϵ�IP
set IP1=%%i
set IP2=%%j
set IP3=%%k
set IP4=%%l

rem ��ȡ���볤�ȼ����ڵ�IP�ӽڵ�λ�ã���1��4�ڣ�
set subMaskLen=%%m
set /a section=%%m / 8
set /a mod=%%m %% 8
if !mod! neq 0 set /a section+=1

rem ���ɶ����Ʊ�ʾ�������ַ����������õ�ŷֳ�4��
call set subMaskStr=%%oneStr:~0,!subMaskLen!%%%%zeroStr:~!subMaskLen!%%
set subMaskStr=!subMaskStr:~0,8!.!subMaskStr:~8,8!.!subMaskStr:~16,8!.!subMaskStr:~24!

rem ��ȡ���������һ���Ǵ�0�Ľڣ���1��4�ڣ������ö����Ʊ�ʾ
set tmpSubMaskStr=!subMaskStr:.= !
set num=0
for %%a in (!tmpSubMaskStr!) do (
set /a num+=1
if !num! equ !section! set mask_section=%%a
)

rem ���ö����Ʊ�ʾ�������е����һ���Ǵ�0�Ľ�תΪʮ����
set sum=0
for /l %%a in (8,-1,1) do (
set multip=1
for /l %%b in (1,1,%%a) do (
set /a multip*=2
)
set /a multip/=2
set /a multip*=!mask_section:~-%%a,1!
set /a sum+=!multip!
)
call set tmpMaskIP=%%IP!section!%%

rem ��ȡ����λ�ϵ�1������IPֵ
set /a "endIP=!sum!^^255^|!tmpMaskIP!"

rem ��ȡ����IP�ֶ�
set /a layer=!section!-1
set "preIP="
for /l %%a in (1,1,!layer!) do (
set preIP=!preIP!.!IP%%a!
)
set /a layer+=1
call set beginIP=%%IP!section!%%

rem ��ȡIP�ķ�Χ�ֶ�
for /f "delims=/" %%a in ("%%x") do set IPstr=%%a
call echo ;!IPstr!��%%IPstr:.!beginIP!.0=.!endIP!.0%%

rem ��������1�ڵ���ʼֵ����ֵֹ֮������IP�б�
for /l %%a in (!beginIP!,1,!endIP!) do (
setlocal
set preIP=!preIP!.%%a
rem call :ListIP
endlocal
)
)
))>result.txt
start result.txt
exit

:ListIP
set /a layer+=1
for /l %%i in (0,1,255) do (
setlocal
if !layer! lss 4 (
set preIP=!preIP!.%%i
call :ListIP
) else (
echo !preIP:~1!.%%i
)
endlocal
)
goto :eof