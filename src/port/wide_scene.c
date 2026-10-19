/* Extended map rendering, with the original 320x200 UI/save coordinates.
 * GPL-3.0-or-later. */
#include "main.h"
#include "wide_scene.h"
#include <stdlib.h>
#include <string.h>

/* Surface copies used by menus carry their map margins with them. Ordinary
 * full-screen backgrounds clear the association, so battle/status/movie
 * screens never reuse the last map's borders. */
typedef struct SceneFrame {
    const SDL_Surface *surface;
    int battle;
    Uint8 pixels[H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT];
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
        memset(f->pixels, 0, sizeof(f->pixels));
    }
    return f;
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
        if (f->surface == surface) { *link = f->next; free(f); return; }
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
