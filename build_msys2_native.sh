#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# build_msys2_native.sh — Uses MSYS2 MinGW64 native GCC + protobuf
# Run from: C:\msys64\mingw64 shell
#   bash /c/Users/parth/Downloads/itantra-m3/build_msys2_native.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

PROJECT="/c/Users/parth/Downloads/itantra-m3"
BUILD="$PROJECT/build_native"
SRC="$PROJECT/src"
PROTO="$PROJECT/proto"

mkdir -p "$BUILD"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         iTantra M3 Phase 1 — MSYS2 Native Build         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

G_VER=$(g++ --version | head -1)
P_VER=$(protoc --version)
echo "Compiler: $G_VER"
echo "protoc  : $P_VER"
echo ""

# Step 1: Generate C++ from proto
echo "[1/4] protoc → C++ sources..."
protoc --proto_path="$PROTO" --cpp_out="$BUILD" "$PROTO/packet_schema.proto"

# Step 2: Compile pb.cc
echo "[2/4] Compiling packet_schema.pb.cc..."
g++ -std=c++17 \
    $(pkg-config --cflags protobuf) \
    -I"$BUILD" \
    -c "$BUILD/packet_schema.pb.cc" \
    -o "$BUILD/packet_schema.pb.o"

# Step 3: Compile sources
echo "[3/4] Compiling PacketEncoder, PacketDecoder, main..."
FLAGS="-std=c++20 -Wall -Wextra -I$SRC -I$BUILD $(pkg-config --cflags protobuf)"

g++ $FLAGS -c "$SRC/PacketEncoder.cpp" -o "$BUILD/PacketEncoder.o"
g++ $FLAGS -c "$SRC/PacketDecoder.cpp" -o "$BUILD/PacketDecoder.o"
g++ $FLAGS -c "$SRC/main.cpp"          -o "$BUILD/main.o"

# Step 4: Link
echo "[4/4] Linking..."
g++ \
    "$BUILD/main.o" \
    "$BUILD/PacketEncoder.o" \
    "$BUILD/PacketDecoder.o" \
    "$BUILD/packet_schema.pb.o" \
    $(pkg-config --libs protobuf) \
    -o "$BUILD/itantra_phase1.exe"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  BUILD COMPLETE → build_native/itantra_phase1.exe       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

"$BUILD/itantra_phase1.exe"
