/* Background-only cover scaling. Fighters, effects and UI retain their
 * original coordinates and uniform 4/3 display scale. GPL-3.0-or-later. */
#include "main.h"
#include "wide_scene.h"
#include <string.h>

static void center_to_legacy(const BYTE *pixels, SDL_Surface *surface)
{
    int y;
    for (y = 0; y < 200; ++y)
        memcpy((BYTE *)surface->pixels + y * surface->pitch,
               pixels + (y + H1PAL_MAP_TOP) * H1PAL_MAP_WIDTH + H1PAL_MAP_LEFT, 320);
}

void h1pal_battle_load_background(SDL_Surface *surface)
{
    BYTE *out = h1pal_scene_battle_frame(surface);
    const BYTE *in = surface->pixels;
    int x, y;
    /* 320x200 -> 360x225 at 9/8, crop 21 rows around the vertical centre.
     * The same rational factor is used for both axes; no horizontal stretch.
     * Source rows 9..189 remain, and no new color/palette entries are needed. */
    for (y = 0; y < H1PAL_MAP_HEIGHT; ++y)
        for (x = 0; x < H1PAL_MAP_WIDTH; ++x)
            out[y * H1PAL_MAP_WIDTH + x] = in[((y * 8 + 84) / 9) * surface->pitch + x * 8 / 9];
    center_to_legacy(out, surface);
}

void h1pal_battle_make_background(void)
{
    BYTE *background = (BYTE *)h1pal_scene_battle_pixels(g_Battle.lpBackground);
    BYTE *pixels;
    SDL_Surface canvas;
    int i, y;
    if (!background) TerminateOnError("Missing extended battle background");
    pixels = h1pal_scene_battle_frame(g_Battle.lpSceneBuf);
    /* Capture persistent magic marks written by the core into the centre. */
    for (y = 0; y < 200; ++y)
        memcpy(background + (y + H1PAL_MAP_TOP) * H1PAL_MAP_WIDTH + H1PAL_MAP_LEFT,
               (BYTE *)g_Battle.lpBackground->pixels + y * g_Battle.lpBackground->pitch, 320);
    for (i = 0; i < H1PAL_MAP_WIDTH * H1PAL_MAP_HEIGHT; ++i) {
        BYTE b = (background[i] & 15) + g_Battle.sBackgroundColorShift;
        if (b & 128) b = 0;
        else if (b & 112) b = 15;
        pixels[i] = (background[i] & 240) | b;
    }
    canvas = *g_Battle.lpSceneBuf;
    canvas.w = canvas.pitch = H1PAL_MAP_WIDTH; canvas.h = H1PAL_MAP_HEIGHT; canvas.pixels = pixels;
    PAL_ApplyWave(&canvas);
    center_to_legacy(pixels, g_Battle.lpSceneBuf);
}

/* Draw RLE sprites into the extended backing frame too. This lets attacks,
 * shadows, summons and other effects cross the old 320-pixel boundary. The
 * legacy canvas remains authoritative for central UI/text and game logic. */
static int extended_canvas(SDL_Surface *surface, SDL_Surface *canvas, PAL_POS *pos)
{
    const BYTE *pixels = h1pal_scene_pixels(surface);
    if (!pixels) return 0;
    *canvas = *surface; canvas->w = canvas->pitch = H1PAL_MAP_WIDTH;
    canvas->h = H1PAL_MAP_HEIGHT; canvas->pixels = (void *)pixels;
    *pos = PAL_XY(PAL_X(*pos) + H1PAL_MAP_LEFT, PAL_Y(*pos) + H1PAL_MAP_TOP);
    return 1;
}
extern INT H1PAL_InternalRLE(LPCBITMAPRLE, SDL_Surface *, PAL_POS);
extern INT H1PAL_InternalRLEShadow(LPCBITMAPRLE, SDL_Surface *, PAL_POS, BOOL);
extern INT H1PAL_InternalRLEShift(LPCBITMAPRLE, SDL_Surface *, PAL_POS, INT);
extern INT H1PAL_InternalRLEMono(LPCBITMAPRLE, SDL_Surface *, PAL_POS, BYTE, INT);

INT PAL_RLEBlitToSurface(LPCBITMAPRLE bitmap, SDL_Surface *surface, PAL_POS pos)
{
    SDL_Surface canvas; PAL_POS shifted = pos;
    if (extended_canvas(surface, &canvas, &shifted)) H1PAL_InternalRLE(bitmap, &canvas, shifted);
    return H1PAL_InternalRLE(bitmap, surface, pos);
}
INT PAL_RLEBlitToSurfaceWithShadow(LPCBITMAPRLE bitmap, SDL_Surface *surface, PAL_POS pos, BOOL shadow)
{
    SDL_Surface canvas; PAL_POS shifted = pos;
    if (extended_canvas(surface, &canvas, &shifted)) H1PAL_InternalRLEShadow(bitmap, &canvas, shifted, shadow);
    return H1PAL_InternalRLEShadow(bitmap, surface, pos, shadow);
}
INT PAL_RLEBlitWithColorShift(LPCBITMAPRLE bitmap, SDL_Surface *surface, PAL_POS pos, INT color)
{
    SDL_Surface canvas; PAL_POS shifted = pos;
    if (extended_canvas(surface, &canvas, &shifted)) H1PAL_InternalRLEShift(bitmap, &canvas, shifted, color);
    return H1PAL_InternalRLEShift(bitmap, surface, pos, color);
}
INT PAL_RLEBlitMonoColor(LPCBITMAPRLE bitmap, SDL_Surface *surface, PAL_POS pos, BYTE color, INT shift)
{
    SDL_Surface canvas; PAL_POS shifted = pos;
    if (extended_canvas(surface, &canvas, &shifted)) H1PAL_InternalRLEMono(bitmap, &canvas, shifted, color, shift);
    return H1PAL_InternalRLEMono(bitmap, surface, pos, color, shift);
}
