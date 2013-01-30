@echo off
setlocal enabledelayedexpansion

rem 生成32位长的纯1和纯0字符串
for /l %%i in (1,1,32) do (
set zeroStr=!zeroStr!0
set oneStr=!oneStr!1
)

nslookup -q=TXT _netblocks.google.com 8.8.8.8>result.txt 2>nul
for /f "delims=" %%i in (result.txt) do set "str=%%i"

rem 剔除字符串中的无关信息
set "str=%str:"=%"
set "str=%str:*ip4:=%"
set "str=%str:ip4:=%"
set "str=%str:?all=%"

echo.&echo 正在生成IP列表，将持续1至数分钟，请耐心等待...

(for %%x in (%str%) do (
echo;&echo ;%%x
for /f "delims=./ tokens=1-5" %%i in ("%%x") do (
rem 获取每节上的IP
set IP1=%%i
set IP2=%%j
set IP3=%%k
set IP4=%%l

rem 获取掩码长度及所在的IP子节点位置（第1～4节）
set subMaskLen=%%m
set /a section=%%m / 8
set /a mod=%%m %% 8
if !mod! neq 0 set /a section+=1

rem 生成二进制表示的掩码字符串，并且用点号分成4节
call set subMaskStr=%%oneStr:~0,!subMaskLen!%%%%zeroStr:~!subMaskLen!%%
set subMaskStr=!subMaskStr:~0,8!.!subMaskStr:~8,8!.!subMaskStr:~16,8!.!subMaskStr:~24!

rem 获取掩码中最后一个非纯0的节（第1～4节），并用二进制表示
set tmpSubMaskStr=!subMaskStr:.= !
set num=0
for %%a in (!tmpSubMaskStr!) do (
set /a num+=1
if !num! equ !section! set mask_section=%%a
)

rem 把用二进制表示的掩码中的最后一个非纯0的节转为十进制
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

rem 获取主机位上第1节最大的IP值
set /a "endIP=!sum!^^255^|!tmpMaskIP!"

rem 获取网络IP字段
set /a layer=!section!-1
set "preIP="
for /l %%a in (1,1,!layer!) do (
set preIP=!preIP!.!IP%%a!
)
set /a layer+=1
call set beginIP=%%IP!section!%%

rem 获取IP的范围字段
for /f "delims=/" %%a in ("%%x") do set IPstr=%%a
call echo ;!IPstr!～%%IPstr:.!beginIP!.0=.!endIP!.0%%

rem 在子网第1节的起始值和终止值之间生成IP列表
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