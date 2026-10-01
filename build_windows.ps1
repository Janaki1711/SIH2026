# ─────────────────────────────────────────────────────────────────────────────
# build_windows.ps1 — iTantra M3 Phase 1 Windows Build Script
#
# Uses: CodeBlocks MinGW-W64 GCC 14 + Anaconda protoc + MSYS2 protobuf
#
# Prerequisites (one-time setup):
#   1. MSYS2 installed at C:\msys64
#   2. Run in MSYS2 MinGW64 shell:
#        pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-protobuf
#
# Or use the all-in-one MSYS2 command:
#   C:\msys64\usr\bin\bash.exe -lc "pacman --noconfirm -S mingw-w64-x86_64-gcc mingw-w64-x86_64-protobuf"
#
# Run from PowerShell:
#   cd C:\Users\parth\Downloads\itantra-m3
#   .\build_windows.ps1
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\parth\Downloads\itantra-m3"
$BuildDir    = "$ProjectRoot\build_native"
$SrcDir      = "$ProjectRoot\src"
$ProtoDir    = "$ProjectRoot\proto"

# ── Detect MSYS2 installation ─────────────────────────────────────────────────
$Msys2Root  = "C:\msys64"
$Msys2GCC   = "$Msys2Root\mingw64\bin\g++.exe"
$Msys2Protoc = "$Msys2Root\mingw64\bin\protoc.exe"
$Msys2Inc   = "$Msys2Root\mingw64\include"
$Msys2Lib   = "$Msys2Root\mingw64\lib"

if (-not (Test-Path $Msys2GCC)) {
    Write-Error "MSYS2 GCC not found at $Msys2GCC. Run: pacman -S mingw-w64-x86_64-gcc"
}
if (-not (Test-Path $Msys2Protoc)) {
    Write-Error "MSYS2 protoc not found at $Msys2Protoc. Run: pacman -S mingw-w64-x86_64-protobuf"
}

Write-Host ""
Write-Host "=========================================================="
Write-Host "         iTantra M3 Phase 1 — Native C++ Build"
Write-Host "=========================================================="
Write-Host ""

$gppVer = & $Msys2GCC --version | Select-Object -First 1
$protocVer = & $Msys2Protoc --version
Write-Host "Compiler: $gppVer"
Write-Host "protoc  : $protocVer"
Write-Host ""

New-Item -ItemType Directory -Force $BuildDir | Out-Null

# ── Step 1: Generate protobuf C++ ─────────────────────────────────────────────
Write-Host "[1/4] Running protoc..."
& $Msys2Protoc `
    --proto_path="$ProtoDir" `
    --cpp_out="$BuildDir" `
    "$ProtoDir\packet_schema.proto"
Write-Host "      Generated packet_schema.pb.h + packet_schema.pb.cc"

# ── Step 2: Compile generated protobuf code ───────────────────────────────────
Write-Host "[2/4] Compiling packet_schema.pb.cc..."
& $Msys2GCC `
    -std=c++17 `
    -I"$Msys2Inc" `
    -I"$BuildDir" `
    -c "$BuildDir\packet_schema.pb.cc" `
    -o "$BuildDir\packet_schema.pb.o"

# ── Step 3: Compile project sources ───────────────────────────────────────────
Write-Host "[3/4] Compiling project sources..."
$CompileFlags = @("-std=c++17", "-Wall", "-I$SrcDir", "-I$BuildDir", "-I$Msys2Inc", "-c")

& $Msys2GCC @CompileFlags "$SrcDir\PacketEncoder.cpp" -o "$BuildDir\PacketEncoder.o"
& $Msys2GCC @CompileFlags "$SrcDir\PacketDecoder.cpp" -o "$BuildDir\PacketDecoder.o"
& $Msys2GCC @CompileFlags "$SrcDir\main.cpp"          -o "$BuildDir\main.o"

# ── Step 4: Link ──────────────────────────────────────────────────────────────
Write-Host "[4/4] Linking itantra_phase1.exe..."
& $Msys2GCC `
    "$BuildDir\main.o" `
    "$BuildDir\PacketEncoder.o" `
    "$BuildDir\PacketDecoder.o" `
    "$BuildDir\packet_schema.pb.o" `
    -L"$Msys2Lib" `
    -lprotobuf -labsl_log_internal_check_op -labsl_log_internal_message -labsl_status -labsl_strings `
    -o "$BuildDir\itantra_phase1.exe"

Write-Host ""
Write-Host "=========================================================="
Write-Host "  Build COMPLETE: $BuildDir\itantra_phase1.exe"
Write-Host "=========================================================="
Write-Host ""
Write-Host "Running Phase 1 demonstration..."
Write-Host ""

# Copy required DLLs next to exe so it runs without PATH setup
$RequiredDlls = @("libprotobuf.dll", "libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll")
foreach ($dll in $RequiredDlls) {
    $src = "$Msys2Root\mingw64\bin\$dll"
    if (Test-Path $src) {
        Copy-Item $src "$BuildDir\" -Force
    }
}

chcp 65001 | Out-Null
& "$BuildDir\itantra_phase1.exe"
