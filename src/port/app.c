/* GPL-3.0-or-later. */
#include "app.h"
#include "native_fs.h"
#include "native_audio.h"
#include "platform.h"
#include "pal_config.h"
#include <setjmp.h>
#include <stdarg.h>
#include <stdio.h>
static jmp_buf return_point;
static int exit_status;
volatile struct h1pal_stats h1pal_stats={0x314c4150,1};
void h1pal_log(const char *format,...) {
    char line[384];va_list ap;va_start(ap,format);
    vsnprintf(line,sizeof(line),format,ap);va_end(ap);
    FILE *f=h1pal_fopen_data("H1PAL.LOG","ab");
    if(f){fputs(line,f);fputs("\n",f);fclose(f);}
}
void h1pal_exit(int status) { exit_status=status;longjmp(return_point,1); }
extern int h1pal_engine_main(void);
int h1_app_main(void) {
    if(!setjmp(return_point)) {
        h1pal_select_data_path();
        FILE *f=h1pal_fopen_data("H1PAL.LOG","wb");if(f)fclose(f);
        h1pal_log("H1PAL 0.1.5 BEGIN");
        h1pal_log("DATA_PATH %s",PAL_H1_DATA_PATH);
        exit_status=h1pal_engine_main();
    }
    h1pal_audio_close();
    h1pal_platform_close();
    h1pal_log("END status=%d frames=%u keys=%u taps=%u",exit_status,h1pal_stats.frames,h1pal_stats.keys,h1pal_stats.taps);
    h1pal_files_close();
    h1pal_allocations_free();
    return exit_status;
}
