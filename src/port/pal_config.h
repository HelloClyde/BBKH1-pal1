#ifndef PAL_H1_CONFIG_H
#define PAL_H1_CONFIG_H

#include <sys/time.h>
#include "data_path.h"

#define PAL_H1_DATA_PATH            h1pal_data_path
#define PAL_PREFIX                    PAL_H1_DATA_PATH
#define PAL_SAVE_PREFIX               PAL_H1_DATA_PATH
#define PAL_CONFIG_PREFIX             PAL_H1_DATA_PATH
#define PAL_PATH_SEPARATORS           "\\/"
#define PAL_IS_PATH_SEPARATOR(c)       ((c) == '\\' || (c) == '/')
#define PAL_FILESYSTEM_IGNORE_CASE     1

#define PAL_DEFAULT_WINDOW_WIDTH       320
#define PAL_DEFAULT_WINDOW_HEIGHT      200
#define PAL_DEFAULT_FULLSCREEN_HEIGHT  200
#define PAL_VIDEO_INIT_FLAGS           (SDL_SWSURFACE | SDL_FULLSCREEN)
#define PAL_SDL_INIT_FLAGS             (SDL_INIT_VIDEO | SDL_INIT_AUDIO)

#define PAL_PLATFORM                   "BBK H1"
#define PAL_CREDIT                     "SDLPAL for H1 contributors"
#define PAL_PORTYEAR                   "2026"

#define PAL_HAS_JOYSTICKS              0
#define PAL_HAS_MOUSE                  0
#define PAL_HAS_TOUCH                  0
#define PAL_HAS_MP3                    0
#define PAL_HAS_OGG                    0
#define PAL_HAS_SDLCD                  0
#define PAL_HAS_NATIVEMIDI             0
#define PAL_HAS_CONFIG_PAGE            0
#define PAL_HAS_PLATFORM_SPECIFIC_UTILS 1
/* The H1 SDL surface already has the game's 320x200 dimensions. TRUE makes
 * SDLPAL use all 200 rows; FALSE reserves the old 240-line display's 40-row
 * letterbox and would squeeze this surface's game content to 160 rows. */
#define PAL_SCALE_SCREEN               TRUE
#define PAL_FORCE_UPDATE_ON_PALETTE_SET 1

void H1PAL_FatalOutput(const char *message);
#define PAL_FATAL_OUTPUT(message) H1PAL_FatalOutput(message)

#endif
