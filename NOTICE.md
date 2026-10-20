# Sources and licenses

H1 SDLPAL port: GPL-3.0-or-later; full text in LICENSE.

The SDL compatibility layer, freestanding libc, PAK reader, AVI bridge, RIX
settings, map pathfinding and resource tools are adapted from HelloClyde's
[BBK9588-pal1](https://github.com/HelloClyde/BBK9588-pal1), commit
10532f74ced55061b6147538dee80797527fb203, GPL-3.0-or-later. The application icon
was redesigned on 2026-10-20 with the built-in GPT Image tool, preserving that
project's red calligraphic 仙 subject and referencing the H1 desktop's glossy
icon style. The original reference is retained as assets/icon-v0.1.4.png;
the prompt and provenance are in assets/icon-prompt.txt and assets/icon-provenance.json.
The 9588 SDK and its firmware addresses are not used by this port.

The SDLPAL core is pinned to
224cb0a0cc839e0e8ecaa299cd480b02b372b9f7. Its checkout stays unmodified;
tools/core_overrides.py generates checked H1 scene/battle/video/menu adaptations in
the build directory, retaining their original copyright headers. Their
GPL-3.0-or-later license is in
third_party/sdlpal/gpl.txt. AdPlug/OPL and the FFmpeg-derived Microsoft Video 1
decoder keep their original file-level GPL/LGPL notices.

H.264 Baseline decoding uses the unmodified H264BSD dependency at commit
42bcb5d753ad86d84903354bf3c68423c28adb7b. The Android Open Source Project
decoder is Apache-2.0; additional wrappers are MIT. Its notices are retained in
third_party/h264bsd/LICENSE.md and the source headers. The full Apache-2.0
license is also included as sdk/LICENSE. The H1 YUV-to-RGB555 bridge is GPL-3.0-or-later.
The existing H1 飞天影音 application was inspected as a format/capability
reference only; no part of its binary, MPlayer or embedded commercial firmware
is copied into this application or its public source distribution.

The H1 native PCM ring, input and game-window interfaces derive from this
workspace's H1 GBA/Arcade platform implementations (GPL-2.0-or-later, combined
here under GPL-3.0-or-later). The H1 BDA SDK is Apache-2.0, pinned in
UPSTREAM.json; its LICENSE and NOTICE remain with the dependency.

Game resources remain under their original proprietary rights. The source
repository, source ZIP and program-only install ZIP contain no game PAK, MKF,
fonts, AVI, firmware or saves. At the user's request, PAL9588.PAK and PALVIDEO.PAK
are provided as separate Release attachments, rebuilt from the user's Steam
installation. Their original rights are retained; the source-code GPL license
does not grant rights to game data. The resource manifest and separate checksums
identify these attachments. A full local installation package can also be rebuilt.
The default v0.1.7 video resource profile uses lossy H.264 Constrained Baseline
inside AVI, preserving original dimensions, frame rate and PCM audio samples.
The optional --video-codec original profile retains the original video pixels.
The synthetic H.264/PCM test fixture contains only a procedural test pattern and
a sine tone, with no game assets. The optional
compact installation package uses the two PAK files the user requested from the
[9588 v0.1.8 release](https://github.com/HelloClyde/BBK9588-pal1/releases/tag/v0.1.8).
Compact files are excluded from the public source and program-only install archives.
Screenshots in docs/evidence show actual
gameplay for documentation; they are not a grant of rights to the game's artwork.

The service-table model in tests/h1_model.py and tests/mxu_model.py was adapted
from this author's H1 GBA test harness. It models native H1 services and MIPS/MXU
instructions; it does not bundle or execute a commercial ROM or firmware dump.
