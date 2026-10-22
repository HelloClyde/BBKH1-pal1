/* Fixed-point, fused 2x-prescale sharp bilinear. GPL-3.0-or-later. */
#ifndef H1PAL_SCALER_H
#define H1PAL_SCALER_H
#include "SDL.h"
typedef struct H1PAL_Sample { Uint16 a, b, weight; } H1PAL_Sample;
void h1pal_scale_axis(H1PAL_Sample *out, unsigned count, unsigned source, unsigned target, unsigned start);
Uint32 h1pal_scale_mix(Uint32 a, Uint32 b, unsigned weight);
void h1pal_scale_indexed(const Uint8 *pixels, unsigned pitch, const Uint32 *palette,
    const H1PAL_Sample *xs, const H1PAL_Sample *ys, unsigned w, unsigned h, volatile Uint32 *out, unsigned stride);
void h1pal_scale_present(const SDL_Surface *surface, const Uint8 *wide, const Uint32 *palette,
    volatile Uint32 *lcd, unsigned w, unsigned h, unsigned left);
void h1pal_scale_shutdown(void);
extern unsigned h1pal_scale_frames, h1pal_scale_total_ms, h1pal_scale_max_ms, h1pal_cover_builds;
#endif
