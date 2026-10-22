/* CPU equivalent of nearest 2x prescale followed by bilinear sampling,
 * fused into one read of the original image. No temporary 2x image or FP.
 * GPL-3.0-or-later. */
#include "scaler.h"
#include "wide_scene.h"
#include <stdlib.h>
#include <string.h>

static H1PAL_Sample xs[480], ys[272];
static unsigned old_w, old_h, old_source_w, old_source_h;
static Uint8 *composed;
unsigned h1pal_scale_frames, h1pal_scale_total_ms, h1pal_scale_max_ms, h1pal_cover_builds;

void h1pal_scale_axis(H1PAL_Sample *out, unsigned count, unsigned source, unsigned target, unsigned start)
{
    for (unsigned i = 0; i < count; ++i) {
        int position = (int)(((2u * (i + start) + 1u) * source * 256u) / (2u * target)) - 128;
        int a = position >> 8, b = a + 1;
        int weight = ((position - a * 256) - 128) * 2 + 128;
        if (weight < 0) weight = 0;
        if (weight > 256) weight = 256;
        if (a < 0) a = 0;
        if (b < 0) b = 0;
        if (a >= (int)source) a = source - 1;
        if (b >= (int)source) b = source - 1;
        out[i].a = a; out[i].b = b; out[i].weight = weight;
    }
}
Uint32 h1pal_scale_mix(Uint32 a, Uint32 b, unsigned weight)
{
    if (!weight || a == b) return a;
    if (weight == 256) return b;
    unsigned inverse = 256 - weight;
    Uint32 rb = ((a & 0xff00ffu) * inverse + (b & 0xff00ffu) * weight + 0x800080u) >> 8;
    Uint32 g = ((a & 0xff00u) * inverse + (b & 0xff00u) * weight + 0x8000u) >> 8;
    return (rb & 0xff00ffu) | (g & 0xff00u);
}
static void row(const Uint8 *in, const Uint32 *palette, const H1PAL_Sample *axis, unsigned w, Uint32 *out)
{
    for (unsigned x = 0; x < w; ++x) {
        H1PAL_Sample s = axis[x];
        out[x] = h1pal_scale_mix(palette[in[s.a]], palette[in[s.b]], s.weight);
    }
}
void h1pal_scale_indexed(const Uint8 *pixels, unsigned pitch, const Uint32 *palette,
    const H1PAL_Sample *xaxis, const H1PAL_Sample *yaxis, unsigned w, unsigned h, volatile Uint32 *out, unsigned stride)
{
    Uint32 rows[2][480];
    int tags[2] = {-1, -1};
    for (unsigned y = 0; y < h; ++y) {
        H1PAL_Sample s = yaxis[y];
        unsigned first = s.a & 1u, second = s.b & 1u;
        if (tags[first] != s.a) { row(pixels + s.a * pitch, palette, xaxis, w, rows[first]); tags[first] = s.a; }
        if (s.weight && tags[second] != s.b) { row(pixels + s.b * pitch, palette, xaxis, w, rows[second]); tags[second] = s.b; }
        for (unsigned x = 0; x < w; ++x)
            out[y * stride + x] = s.weight ? h1pal_scale_mix(rows[first][x], rows[second][x], s.weight) : rows[first][x];
    }
}
void h1pal_scale_present(const SDL_Surface *surface, const Uint8 *wide, const Uint32 *palette,
    volatile Uint32 *lcd, unsigned w, unsigned h, unsigned left)
{
    const Uint8 *pixels = surface->pixels;
    unsigned pitch = surface->pitch, sw = surface->w, sh = surface->h;
    H1PAL_CoverView cover = {0};
    if (wide) {
        if (!composed) composed = malloc(H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT);
        if (!composed) return;
        memcpy(composed, wide, H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT);
        for (unsigned y = 0; y < 200; ++y)
            memcpy(composed + (y + H1PAL_MAP_TOP) * H1PAL_MAP_WIDTH + H1PAL_MAP_LEFT, pixels + y * pitch, 320);
        pixels = composed; pitch = sw = H1PAL_MAP_WIDTH; sh = H1PAL_MAP_HEIGHT;
        h1pal_scene_cover_view(surface, palette, &cover);
    }
    if (w != old_w || h != old_h || sw != old_source_w || sh != old_source_h) {
        h1pal_scale_axis(xs, w, sw, w, 0); h1pal_scale_axis(ys, h, sh, h, 0);
        old_w = w; old_h = h; old_source_w = sw; old_source_h = sh;
    }
    if (!cover.rgb) {
        h1pal_scale_indexed(pixels, pitch, palette, xs, ys, w, h, lcd + left, 480);
        return;
    }
    /* Unpainted background samples come from the original 320x200 image's
     * single-pass output. The legacy canvas remains authoritative for text,
     * sprites, effects and the engine's original coordinate system. */
    for (unsigned y = 0; y < h; ++y) {
        H1PAL_Sample sy = ys[y];
        unsigned arow = sy.a * pitch, brow = sy.b * pitch;
        for (unsigned x = 0; x < w; ++x) {
            H1PAL_Sample sx = xs[x];
            unsigned aa = arow + sx.a, ab = arow + sx.b, ba = brow + sx.a, bb = brow + sx.b;
            Uint32 base = cover.rgb[y * 480 + x], a, b, c, d;
            a = pixels[aa] == cover.reference[aa] ? base : palette[pixels[aa]];
            b = pixels[ab] == cover.reference[ab] ? base : palette[pixels[ab]];
            c = pixels[ba] == cover.reference[ba] ? base : palette[pixels[ba]];
            d = pixels[bb] == cover.reference[bb] ? base : palette[pixels[bb]];
            lcd[y * 480 + x] = h1pal_scale_mix(h1pal_scale_mix(a, b, sx.weight), h1pal_scale_mix(c, d, sx.weight), sy.weight);
        }
    }
}
void h1pal_scale_shutdown(void)
{
    free(composed); composed = NULL;
    old_w = old_h = old_source_w = old_source_h = 0;
}
