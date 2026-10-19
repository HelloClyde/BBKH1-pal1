/* H1 V1.41 firmware binding. GPL-3.0-or-later. */
#ifndef H1PAL_NATIVE_FS_H
#define H1PAL_NATIVE_FS_H
#include "h1_sdk.h"
static inline int h1pal_fs_file_is_valid(int h) { return h && h!=-1; }
static inline int h1pal_fs_fopen_raw(const char *p,const char *m) { return (int)h1_fopen(p,m); }
static inline int h1pal_fs_close_raw(int h) { return h1_fclose((h1_file *)h); }
static inline int h1pal_fs_fread_raw(void *p,unsigned s,unsigned n,int h) {
    if(!s||!n)return 0;if(n>0x7fffffffu/s)return -1;
    unsigned got=h1_fread(p,1,s*n,(h1_file *)h);return got>s*n?-1:(int)(got/s);
}
static inline int h1pal_fs_fwrite_raw(const void *p,unsigned s,unsigned n,int h) {
    if(!s||!n)return 0;if(n>0x7fffffffu/s)return -1;
    unsigned got=h1_fwrite(p,1,s*n,(h1_file *)h);return got>s*n?-1:(int)(got/s);
}
static inline int h1pal_fs_seek_raw(int h,int o,int w) { return h1_fseek((h1_file *)h,o,w); }
static inline int h1pal_fs_tell_raw(int h) { return h1_ftell((h1_file *)h); }
/* Read/write wrappers retain per-stream errors; no unverified firmware ABI. */
static inline int h1pal_fs_error(int h) { (void)h;return 0; }
static inline int h1pal_fs_chdir(const char *p) { (void)p;return -1; }
void h1pal_exit(int status) __attribute__((noreturn));
void h1pal_files_close(void);
void h1pal_allocations_free(void);
#endif
