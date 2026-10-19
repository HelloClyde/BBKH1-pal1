#ifndef H1PAL_PLATFORM_H
#define H1PAL_PLATFORM_H

#include "SDL.h"

int h1pal_platform_open(void);
void h1pal_platform_close(void);
void h1pal_platform_present(const SDL_Surface *surface);
void h1pal_platform_present_rgb555(
    const Uint16 *pixels, int width, int height, int pitch_pixels
);
void h1pal_platform_pump(void);
unsigned h1pal_platform_keys(void);
int h1pal_platform_take_tap(int *logical_x, int *logical_y);
void h1pal_platform_wait_action_release(void);
int h1pal_platform_detached(void);
Uint32 h1pal_platform_ticks(void);
void h1pal_platform_delay(Uint32 milliseconds);

#endif
