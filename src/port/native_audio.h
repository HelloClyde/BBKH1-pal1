#ifndef H1PAL_NATIVE_AUDIO_H
#define H1PAL_NATIVE_AUDIO_H
#include <stdint.h>
int h1pal_audio_open(unsigned rate);
int h1pal_audio_ready(unsigned frames);
int h1pal_audio_write(const int16_t *mono,unsigned frames);
void h1pal_audio_close(void);
void h1pal_audio_pause(int paused);
#endif
