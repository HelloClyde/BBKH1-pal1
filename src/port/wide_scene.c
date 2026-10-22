/* Extended map rendering, with the original 320x200 UI/save coordinates.
 * GPL-3.0-or-later. */
#include "main.h"
#include "wide_scene.h"
#include "scaler.h"
#include <stdlib.h>
#include <string.h>

/* Surface copies used by menus carry their map margins with them. Ordinary
 * full-screen backgrounds clear the association, so battle/status/movie
 * screens never reuse the last map's borders. */
typedef struct CoverImage {
    unsigned references;
    Uint8 original[320 * 200];
    Uint32 *rgb;
    Uint32 palette[256];
    int palette_valid, color_shift;
} CoverImage;
typedef struct SceneFrame {
    const SDL_Surface *surface;
    int battle;
    Uint8 pixels[H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT];
    CoverImage *cover;
    Uint16 *reference;
    int color_shift;
    int saved_x, saved_y;
    struct SceneFrame *next;
} SceneFrame;
static SceneFrame *frames;
static SDL_Surface *wide, *legacy;
static PAL_POS viewport;
static PARTY party[MAX_PLAYABLE_PLAYER_ROLES];
#if H1PAL_REGRESSION
int h1pal_scene_test_legacy;
#endif

static SceneFrame *find(const SDL_Surface *surface)
{
    SceneFrame *f;
    for (f = frames; f; f = f->next) if (f->surface == surface) return f;
    return NULL;
}
static SceneFrame *attach(const SDL_Surface *surface)
{
    SceneFrame *f = find(surface);
    if (!f) {
        f = malloc(sizeof(*f));
        if (!f) TerminateOnError("Cannot allocate extended map frame");
        f->surface = surface; f->battle = 0; f->next = frames; frames = f;
        f->cover = NULL; f->reference = NULL; f->color_shift = 0;
        f->saved_x = f->saved_y = 0;
        memset(f->pixels, 0, sizeof(f->pixels));
    }
    return f;
}
static void release_cover(SceneFrame *f)
{
    if (f->cover && --f->cover->references == 0) {
        free(f->cover->rgb); free(f->cover);
    }
    f->cover = NULL;
}
static void reference_buffer(SceneFrame *f)
{
    if (!f->reference) f->reference = malloc(sizeof(Uint16) * H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT);
    if (!f->reference) TerminateOnError("Cannot allocate cover reference");
}
static void copy_cover(SceneFrame *from, SceneFrame *to)
{
    if (from == to) return;
    release_cover(to);
    if (!from->cover) return;
    to->cover = from->cover; ++to->cover->references;
    to->color_shift = from->color_shift;
    to->saved_x = from->saved_x; to->saved_y = from->saved_y;
    reference_buffer(to);
    memcpy(to->reference, from->reference, sizeof(Uint16) * H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT);
}
void h1pal_scene_cover_begin(SDL_Surface *surface)
{
    SceneFrame *f = attach(surface);
    release_cover(f);
    f->cover = calloc(1, sizeof(*f->cover));
    if (!f->cover) TerminateOnError("Cannot retain original background");
    f->cover->references = 1;
    f->saved_x = f->saved_y = 0;
    for (unsigned y = 0; y < 200; ++y)
        memcpy(f->cover->original + y * 320, (Uint8 *)surface->pixels + y * surface->pitch, 320);
}
void h1pal_scene_cover_reference(SDL_Surface *surface, int color_shift)
{
    SceneFrame *f = find(surface);
    if (!f || !f->cover) return;
    reference_buffer(f); f->color_shift = color_shift;
    for (unsigned i = 0; i < H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT; ++i) f->reference[i] = f->pixels[i];
}
void h1pal_scene_cover_copy(SDL_Surface *source, SDL_Surface *destination, int color_shift)
{
    SceneFrame *from = find(source), *to = find(destination);
    if (!to) return;
    if (!from || !from->cover) { release_cover(to); return; }
    copy_cover(from, to); to->color_shift = color_shift;
    if (color_shift) for (unsigned i = 0; i < H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT; ++i) {
        unsigned c = to->reference[i];
        if (c < 256) {
            int low = (c & 15) + color_shift;
            if (low < 0) low = 0;
            if (low > 15) low = 15;
            to->reference[i] = (c & 240) | low;
        }
    }
}
void h1pal_scene_cover_drop(SDL_Surface *surface)
{
    SceneFrame *f = find(surface); if (f) release_cover(f);
}
void h1pal_scene_cover_dirty(SDL_Surface *surface, int x, int y, int w, int h)
{
    SceneFrame *f = find(surface);
    if (!f || !f->cover || !f->reference) return;
    x += H1PAL_MAP_LEFT; y += H1PAL_MAP_TOP;
    int right = x + w, bottom = y + h;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (right > H1PAL_MAP_WIDTH) right = H1PAL_MAP_WIDTH;
    if (bottom > H1PAL_MAP_HEIGHT) bottom = H1PAL_MAP_HEIGHT;
    for (int row = y; row < bottom; ++row)
        for (int col = x; col < right; ++col) f->reference[row * H1PAL_MAP_WIDTH + col] = 256;
}
void h1pal_scene_cover_blit(SDL_Surface *source, const SDL_Rect *from, SDL_Surface *destination, const SDL_Rect *to)
{
    SceneFrame *f = find(source), *d = find(destination);
    /* PAL saves menu boxes as smaller SDL surfaces. Carry the matching mask
     * through these saves so closing nested menus restores direct scaling. */
    if (f && f->cover && (destination->w != 320 || destination->h != 200)) {
        d = attach(destination); d->battle = f->battle;
        copy_cover(f, d);
        d->saved_x = f->saved_x + from->x - to->x;
        d->saved_y = f->saved_y + from->y - to->y;
        return;
    }
    if (f && d && f->cover && f->cover == d->cover) {
        for (int y = 0; y < from->h; ++y) {
            int sy = f->saved_y + from->y + y + H1PAL_MAP_TOP;
            int dy = d->saved_y + to->y + y + H1PAL_MAP_TOP;
            if (sy < 0 || sy >= H1PAL_MAP_HEIGHT || dy < 0 || dy >= H1PAL_MAP_HEIGHT) continue;
            for (int x = 0; x < from->w; ++x) {
                int sx = f->saved_x + from->x + x + H1PAL_MAP_LEFT;
                int dx = d->saved_x + to->x + x + H1PAL_MAP_LEFT;
                if (sx >= 0 && sx < H1PAL_MAP_WIDTH && dx >= 0 && dx < H1PAL_MAP_WIDTH)
                    d->reference[dy * H1PAL_MAP_WIDTH + dx] = f->reference[sy * H1PAL_MAP_WIDTH + sx];
            }
        }
    } else h1pal_scene_cover_dirty(destination, to->x, to->y, from->w, from->h);
}
void h1pal_scene_cover_view(const SDL_Surface *surface, const Uint32 *palette, H1PAL_CoverView *view)
{
    SceneFrame *f = find(surface);
    view->rgb = NULL; view->reference = NULL;
    if (!f || !f->cover || !f->reference) return;
    CoverImage *cover = f->cover;
    if (!cover->rgb) cover->rgb = malloc(480 * 272 * sizeof(Uint32));
    if (!cover->rgb) return;
    if (!cover->palette_valid || cover->color_shift != f->color_shift || memcmp(cover->palette, palette, sizeof(cover->palette))) {
        H1PAL_Sample xaxis[480], yaxis[272];
        Uint32 colors[256];
        for (unsigned i = 0; i < 256; ++i) {
            int low = (i & 15) + f->color_shift;
            if (low < 0) low = 0;
            if (low > 15) low = 15;
            colors[i] = palette[(i & 240) | low];
        }
        h1pal_scale_axis(xaxis, 480, 320, 480, 0);
        /* Uniform 1.5x cover: 320x200 -> 480x300, crop 14 LCD rows per side. */
        h1pal_scale_axis(yaxis, 272, 200, 300, 14);
        h1pal_scale_indexed(cover->original, 320, colors, xaxis, yaxis, 480, 272, cover->rgb, 480);
        memcpy(cover->palette, palette, sizeof(cover->palette));
        cover->color_shift = f->color_shift; cover->palette_valid = 1; ++h1pal_cover_builds;
    }
    view->rgb = cover->rgb; view->reference = f->reference;
}
const Uint8 *h1pal_scene_pixels(const SDL_Surface *surface)
{
    SceneFrame *f = find(surface);
    return f && (f->battle == 2 || f->battle == !!(gpGlobals && gpGlobals->fInBattle)) ? f->pixels : NULL;
}
Uint8 *h1pal_scene_battle_frame(SDL_Surface *surface)
{
    SceneFrame *f = attach(surface); f->battle = 1; return f->pixels;
}
const Uint8 *h1pal_scene_battle_pixels(const SDL_Surface *surface)
{
    SceneFrame *f = find(surface); return f && f->battle == 1 ? f->pixels : NULL;
}
Uint8 *h1pal_scene_ui_frame(SDL_Surface *surface)
{
    SceneFrame *f = attach(surface); f->battle = 2; return f->pixels;
}
void h1pal_scene_free(SDL_Surface *surface)
{
    SceneFrame **link = &frames;
    while (*link) {
        SceneFrame *f = *link;
        if (f->surface == surface) { *link = f->next; release_cover(f); free(f->reference); free(f); return; }
        link = &f->next;
    }
}
void h1pal_scene_clear(SDL_Surface *surface) { h1pal_scene_free(surface); }
void h1pal_scene_copy(SDL_Surface *source, SDL_Surface *destination)
{
    SceneFrame *f;
    if (source == destination) return;
    f = find(source);
    if (f) { SceneFrame *to = attach(destination); to->battle = f->battle;
             copy_cover(f, to);
             memcpy(to->pixels, f->pixels, sizeof(f->pixels)); }
    else h1pal_scene_clear(destination);
}
void h1pal_scene_shift(SDL_Surface *source, SDL_Surface *destination, int y_offset)
{
    SceneFrame *f = find(source), *to;
    int y;
    if (!f) { h1pal_scene_clear(destination); return; }
    if (source == destination) return;
    to = attach(destination);
    release_cover(to);
    to->battle = f->battle;
    memset(to->pixels, 0, sizeof(to->pixels));
    for (y = 0; y < H1PAL_MAP_HEIGHT; ++y) {
        int sy = y - y_offset;
        if (sy >= 0 && sy < H1PAL_MAP_HEIGHT)
            memcpy(to->pixels + y * H1PAL_MAP_WIDTH,
                   f->pixels + sy * H1PAL_MAP_WIDTH, H1PAL_MAP_WIDTH);
    }
}
void h1pal_scene_switch(SDL_Surface *source, SDL_Surface *destination, int phase)
{
    SceneFrame *f = find(source), *to;
    unsigned i;
    if (!f) { h1pal_scene_clear(destination); return; }
    to = attach(destination); to->battle = f->battle;
    for (i = phase; i < sizeof(f->pixels); i += 6) to->pixels[i] = f->pixels[i];
    if (!memcmp(f->pixels, to->pixels, sizeof(f->pixels))) copy_cover(f, to);
    else release_cover(to);
}
void h1pal_scene_fade(SDL_Surface *source, SDL_Surface *destination, int phase, int pass)
{
    SceneFrame *f = find(source), *to;
    unsigned k;
    if (!f) { h1pal_scene_clear(destination); return; }
    to = attach(destination); to->battle = f->battle;
    for (k = phase; k < sizeof(f->pixels); k += 6) {
        BYTE a = f->pixels[k], b = to->pixels[k];
        if (pass > 0) {
            if ((a & 15) > (b & 15)) ++b;
            else if ((a & 15) < (b & 15)) --b;
        }
        to->pixels[k] = (a & 240) | (b & 15);
    }
    if (!memcmp(f->pixels, to->pixels, sizeof(f->pixels))) copy_cover(f, to);
    else release_cover(to);
}
void h1pal_scene_begin(void)
{
    unsigned i;
#if H1PAL_REGRESSION
    if (h1pal_scene_test_legacy) { legacy = NULL; h1pal_scene_clear(gpScreen); return; }
#endif
    if (!wide) {
        wide = SDL_CreateRGBSurface(0, H1PAL_MAP_WIDTH, H1PAL_MAP_HEIGHT, 8, 0, 0, 0, 0);
        if (!wide) TerminateOnError("Cannot allocate extended map canvas");
    }
    legacy = gpScreen; gpScreen = wide;
    viewport = gpGlobals->viewport;
    memcpy(party, gpGlobals->rgParty, sizeof(party));
    gpGlobals->viewport = PAL_XY(PAL_X(viewport) - H1PAL_MAP_LEFT,
                                PAL_Y(viewport) - H1PAL_MAP_TOP);
    for (i = 0; i < MAX_PLAYABLE_PLAYER_ROLES; ++i) {
        gpGlobals->rgParty[i].x += H1PAL_MAP_LEFT;
        gpGlobals->rgParty[i].y += H1PAL_MAP_TOP;
    }
    SDL_FillRect(wide, NULL, 0);
}
void h1pal_scene_end(void)
{
    SDL_Rect crop = {H1PAL_MAP_LEFT, H1PAL_MAP_TOP, 320, 200};
    if (!legacy) return;
    gpGlobals->viewport = viewport;
    memcpy(gpGlobals->rgParty, party, sizeof(party));
    gpScreen = legacy; legacy = NULL;
    SDL_BlitSurface(wide, &crop, gpScreen, NULL);
    SceneFrame *f = attach(gpScreen); f->battle = 0;
    release_cover(f);
    memcpy(f->pixels, wide->pixels, H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT);
}
void h1pal_scene_shutdown(void)
{
    if (wide) SDL_FreeSurface(wide);
    wide = NULL;
    while (frames) h1pal_scene_free((SDL_Surface *)frames->surface);
}

extern INT H1PAL_InternalFBPBlit(LPBYTE bitmap, SDL_Surface *surface);
INT PAL_FBPBlitToSurface(LPBYTE bitmap, SDL_Surface *surface)
{
    h1pal_scene_clear(surface);
    return H1PAL_InternalFBPBlit(bitmap, surface);
}
