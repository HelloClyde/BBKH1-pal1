/* User-configurable H1 controls. GPL-3.0-or-later. */
#ifndef H1PAL_KEYMAP_H
#define H1PAL_KEYMAP_H
#define H1PAL_KEY_COUNT 6
unsigned h1pal_keymap_normalize(unsigned key);
unsigned h1pal_keymap_get(unsigned action);
unsigned h1pal_keymap_default(unsigned action);
unsigned h1pal_keymap_action(unsigned key, int defaults);
void h1pal_keymap_load(void);
int h1pal_keymap_assign(unsigned action, unsigned key);
int h1pal_keymap_restore(void);
void H1PAL_KeymapMenu(void);
#endif
