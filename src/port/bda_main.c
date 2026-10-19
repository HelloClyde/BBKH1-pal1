#include "pal_config.h"
#include <stdio.h>

int sdlpal_main(int argc, char *argv[]);

__attribute__((section(".text.bda_main")))
int h1pal_engine_main(void)
{
    char executable[128];
    snprintf(executable,sizeof(executable),"%sSDLPAL.BDA",PAL_H1_DATA_PATH);
    char *arguments[] = { executable, 0 };
    return sdlpal_main(1, arguments);
}
