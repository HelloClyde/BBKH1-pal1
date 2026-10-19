/* H1 application data volume selection. GPL-3.0-or-later. */
#ifndef H1PAL_DATA_PATH_H
#define H1PAL_DATA_PATH_H

#include <stdio.h>

/* Firmware paths use GBK bytes, independently of the source-file encoding. */
#define H1PAL_DATA_DIRECTORY "\\\xd3\xa6\xd3\xc3\\\xca\xfd\xbe\xdd\\PAL\\"
#define H1PAL_DEFAULT_DATA_PATH "A:" H1PAL_DATA_DIRECTORY

#ifdef __cplusplus
extern "C" {
#endif
extern char h1pal_data_path[];
/* Call once before opening logs, configuration or resource archives. */
int h1pal_select_data_path(void);
FILE *h1pal_fopen_data(const char *name, const char *mode);
#ifdef __cplusplus
}
#endif

#endif
