/* Full-width menu backgrounds, with uniformly scaled text/portraits/icons.
 * GPL-3.0-or-later. */
#include "main.h"
#include "wide_scene.h"
#include <string.h>

void h1pal_ui_background(SDL_Surface *surface, int cover)
{
    Uint8 *out;
    const Uint8 *in;
    int x, y;
    if (!surface || surface->w != 320 || surface->h != 200) return;
    out = h1pal_scene_ui_frame(surface); in = surface->pixels;
    if (cover) {
        /* Title art is decorative: use uniform 9/8 cover, as in battle. */
        for (y = 0; y < H1PAL_MAP_HEIGHT; ++y)
            for (x = 0; x < H1PAL_MAP_WIDTH; ++x)
                out[y * H1PAL_MAP_WIDTH + x] = in[((y * 8 + 84) / 9) * surface->pitch + x * 8 / 9];
        for (y = 0; y < 200; ++y)
            memcpy((Uint8 *)surface->pixels + y * surface->pitch,
                   out + (y + H1PAL_MAP_TOP) * H1PAL_MAP_WIDTH + H1PAL_MAP_LEFT, 320);
    } else {
        /* Status/equipment FBP art contains baked-in slots and labels.
         * Preserve every central pixel. Extend only the empty texture using
         * its clear rightmost 8-pixel strip; do not repeat the avatar frame. */
        for (y = 0; y < H1PAL_MAP_HEIGHT; ++y) {
            int sy = y - H1PAL_MAP_TOP;
            if (sy < 0) sy = 0;
            if (sy >= 200) sy = 199;
            for (x = 0; x < H1PAL_MAP_WIDTH; ++x) {
                int sx = x - H1PAL_MAP_LEFT;
                if (sx < 0 || sx >= 320) sx = 312 + ((sx + 320) & 7);
                out[y * H1PAL_MAP_WIDTH + x] = in[sy * surface->pitch + sx];
            }
        }
    }
}

void h1pal_ui_cursor(SDL_Surface *surface, int text_x, int text_y)
{
    int pass, y;
    int top = text_y + (PAL_FontHeight() - 7) / 2;
    /* A right-pointing marker sits in the text's left gutter. The original
     * up-arrow occupied the last six rows of the 16-pixel Chinese glyphs. */
    for (pass = 1; pass >= 0; --pass)
        for (y = 0; y < 7; ++y) {
            int distance = y < 3 ? 3 - y : y - 3;
            SDL_Rect row = {text_x - 6 + pass, top + y + pass, 4 - distance, 1};
            SDL_FillRect(surface, &row, pass ? 0 : 63);
        }
}

int h1pal_ui_equipment_offset(unsigned item, int slot)
{
    const WCHAR *name = PAL_GetWord(item);
    int width = 0, x;
    while (*name) width += PAL_CharWidth(*name++);
    x = PAL_X(gConfig.ScreenLayout.RoleEquipImageBoxes[slot]) + 25 - width / 2;
    if (x + width > 320) x = 320 - width;
    if (x < 0) x = 0;
    return x - PAL_X(gConfig.ScreenLayout.RoleEquipNames[slot]);
}
