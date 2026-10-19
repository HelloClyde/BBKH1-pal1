/* H1 map viewport extension. GPL-3.0-or-later. */
#ifndef H1PAL_WIDE_SCENE_H
#define H1PAL_WIDE_SCENE_H
#include "SDL.h"
#define H1PAL_MAP_WIDTH 360
#define H1PAL_MAP_HEIGHT 204
#define H1PAL_MAP_LEFT 20
#define H1PAL_MAP_TOP 2
void h1pal_scene_begin(void);
void h1pal_scene_end(void);
void h1pal_scene_clear(SDL_Surface *surface);
void h1pal_scene_copy(SDL_Surface *source, SDL_Surface *destination);
void h1pal_scene_shift(SDL_Surface *source, SDL_Surface *destination, int y_offset);
void h1pal_scene_free(SDL_Surface *surface);
void h1pal_scene_shutdown(void);
const Uint8 *h1pal_scene_pixels(const SDL_Surface *surface);
Uint8 *h1pal_scene_battle_frame(SDL_Surface *surface);
const Uint8 *h1pal_scene_battle_pixels(const SDL_Surface *surface);
Uint8 *h1pal_scene_ui_frame(SDL_Surface *surface);
void h1pal_ui_background(SDL_Surface *surface, int cover);
void h1pal_ui_cursor(SDL_Surface *surface, int text_x, int text_y);
int h1pal_ui_equipment_offset(unsigned item, int slot);
void h1pal_scene_fade(SDL_Surface *source, SDL_Surface *destination, int phase, int pass);
void h1pal_scene_switch(SDL_Surface *source, SDL_Surface *destination, int phase);
void h1pal_battle_load_background(SDL_Surface *surface);
void h1pal_battle_make_background(void);
#endif
