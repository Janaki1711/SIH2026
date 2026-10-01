# iTantra M3 — Generated Directory

This directory is populated **at build time** by CMake calling `protoc`.

Do not manually place files here.

## What gets generated here

When you run `cmake --build .`, CMake invokes:

```
protoc --cpp_out=<build_dir> proto/packet_schema.proto
```

This produces:
- `packet_schema.pb.h`  — C++ header for VoicePacket, PriorityLevel
- `packet_schema.pb.cc` — C++ implementation (serialization/deserialization)

These files are referenced by:
- `src/PacketEncoder.hpp` → `#include "packet_schema.pb.h"`
- `src/PacketDecoder.hpp` → `#include "packet_schema.pb.h"`
