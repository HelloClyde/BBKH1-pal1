#ifndef H1PAL_H264_VIDEO_H
#define H1PAL_H264_VIDEO_H
#include "SDL.h"
void h1pal_h264_reset(void);
void h1pal_h264_close(void);
int h1pal_h264_failed(void);
int h1pal_h264_decode(SDL_Surface *surface, unsigned char *data, unsigned length);
extern unsigned h1pal_h264_frames,h1pal_h264_max_ms,h1pal_h264_total_ms;
#endif
