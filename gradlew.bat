@rem
@rem Copyright 2015 the original author or authors.
@rem
@rem Licensed under the Apache License, Version 2.0 (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem      https://www.apache.org/licenses/LICENSE-2.0
@rem
@rem Unless required by applicable law or agreed to in writing, software
@rem distributed under the License is distributed on an "AS IS" BASIS,
@rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@rem See the License for the specific language governing permissions and
@rem limitations under the License.
@rem

@if "%DEBUG%"=="" @echo off
if "%OS%"=="Windows_NT" setlocal

set DIRNAME=%~dp0
if "%DIRNAME%"=="" set DIRNAME=.
set MAIN_CLASS=org.gradle.wrapper.GradleWrapperMain

@rem Set JAVA_HOME explicitly to JDK 21 for Gradle 8.10 compatibility
if exist "C:\Users\chhav\.jdks\jbr-21.0.11\bin\java.exe" (
    set "JAVA_HOME=C:\Users\chhav\.jdks\jbr-21.0.11"
    set "JAVA_EXE=C:\Users\chhav\.jdks\jbr-21.0.11\bin\java.exe"
    goto execute
)

if defined JAVA_HOME goto findJavaFromJavaHome

set JAVA_EXE=java.exe
%JAVA_EXE% -version >NUL 2>&1
if %ERRORLEVEL% equ 0 goto execute

goto fail

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

if exist "%JAVA_EXE%" goto execute

:fail
echo.
echo ERROR: JAVA_HOME is not set properly.
goto failEnd

:execute
set CLASSPATH=%DIRNAME%\gradle\wrapper\gradle-wrapper.jar

"%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %GRADLE_OPTS% "-Dorg.gradle.appname=%APP_BASE_NAME%" -classpath "%CLASSPATH%" %MAIN_CLASS% %*

:failEnd
if "%OS%"=="Windows_NT" endlocal
