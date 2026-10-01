#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# build.sh — iTantra M3 Phase 1 Build Script (MSYS2 MinGW64)
#
# Run this from the MSYS2 MinGW64 shell after:
#   pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-protobuf cmake make
#
# Usage:
#   cd /c/Users/parth/Downloads/itantra-m3
#   bash build.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build_msys2"
PROTO_DIR="$SCRIPT_DIR/proto"
SRC_DIR="$SCRIPT_DIR/src"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         iTantra M3 Phase 1 — Build Script               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

mkdir -p "$BUILD_DIR"

# ── Step 1: Generate protobuf C++ sources ─────────────────────────────────────
echo "[1/4] Running protoc..."
protoc \
    --proto_path="$PROTO_DIR" \
    --cpp_out="$BUILD_DIR" \
    "$PROTO_DIR/packet_schema.proto"
echo "      Generated: packet_schema.pb.h, packet_schema.pb.cc"

# ── Step 2: Compile protobuf generated code ───────────────────────────────────
echo "[2/4] Compiling packet_schema.pb.cc..."
g++ -std=c++17 \
    -I"$(pkg-config --cflags-only-I protobuf | sed 's/-I//g')" \
    -I"$BUILD_DIR" \
    -c "$BUILD_DIR/packet_schema.pb.cc" \
    -o "$BUILD_DIR/packet_schema.pb.o"

# ── Step 3: Compile project sources ───────────────────────────────────────────
echo "[3/4] Compiling project sources..."

CXXFLAGS="-std=c++17 -Wall -I$SRC_DIR -I$BUILD_DIR $(pkg-config --cflags protobuf)"

g++ $CXXFLAGS -c "$SRC_DIR/PacketEncoder.cpp" -o "$BUILD_DIR/PacketEncoder.o"
g++ $CXXFLAGS -c "$SRC_DIR/PacketDecoder.cpp" -o "$BUILD_DIR/PacketDecoder.o"
g++ $CXXFLAGS -c "$SRC_DIR/main.cpp"          -o "$BUILD_DIR/main.o"

# ── Step 4: Link ──────────────────────────────────────────────────────────────
echo "[4/4] Linking itantra_phase1.exe..."
g++ \
    "$BUILD_DIR/main.o" \
    "$BUILD_DIR/PacketEncoder.o" \
    "$BUILD_DIR/PacketDecoder.o" \
    "$BUILD_DIR/packet_schema.pb.o" \
    $(pkg-config --libs protobuf) \
    -o "$BUILD_DIR/itantra_phase1.exe"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Build COMPLETE                                          ║"
echo "║  Binary: build_msys2/itantra_phase1.exe                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Running Phase 1 demonstration..."
echo ""
"$BUILD_DIR/itantra_phase1.exe"
