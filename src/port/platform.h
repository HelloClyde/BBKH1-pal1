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
void h1pal_platform_wait_input_release(void);
void h1pal_platform_settings_input(int enabled);
void h1pal_platform_capture_keys(int enabled);
unsigned h1pal_platform_take_capture_key(void);
int h1pal_platform_detached(void);
Uint32 h1pal_platform_ticks(void);
void h1pal_platform_delay(Uint32 milliseconds);

#endif
