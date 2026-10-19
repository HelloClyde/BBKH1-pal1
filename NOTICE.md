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

The H1 native PCM ring, input and game-window interfaces derive from this
workspace's H1 GBA/Arcade platform implementations (GPL-2.0-or-later, combined
here under GPL-3.0-or-later). The H1 BDA SDK is Apache-2.0, pinned in
UPSTREAM.json; its LICENSE and NOTICE remain with the dependency.

Game resources remain under their original proprietary rights. This public
repository and its Release contain no game PAK, MKF, fonts, AVI, firmware or saves.
The local-only full installation package can be rebuilt from the user's Steam installation.
Original AVI video retains its decoded pixels and frame rate. The optional
compact installation package uses the two PAK files the user requested from the
[9588 v0.1.8 release](https://github.com/HelloClyde/BBK9588-pal1/releases/tag/v0.1.8).
Those files are excluded from public source and Release archives. No game resource
packages have been published by this work. Screenshots in docs/evidence show actual
gameplay for documentation; they are not a grant of rights to the game's artwork.

The service-table model in tests/h1_model.py and tests/mxu_model.py was adapted
from this author's H1 GBA test harness. It models native H1 services and MIPS/MXU
instructions; it does not bundle or execute a commercial ROM or firmware dump.
