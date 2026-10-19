#ifndef H1PAL_APP_H
#define H1PAL_APP_H
void h1pal_log(const char *format,...);
void h1pal_exit(int status) __attribute__((noreturn));
extern volatile struct h1pal_stats {
    unsigned magic,version,frames,keys,taps,audio_batches,audio_underruns,error;
} h1pal_stats;
#endif
