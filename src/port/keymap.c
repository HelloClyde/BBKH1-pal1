/* Persistent six-action mapping; selected data volume owns the file.
 * GPL-3.0-or-later. */
#include "keymap.h"
#include "data_path.h"
#include <stdio.h>
#include <string.h>

static const unsigned defaults[H1PAL_KEY_COUNT] = {37, 27, 40, 35, 25, 24};
static unsigned bindings[H1PAL_KEY_COUNT] = {37, 27, 40, 35, 25, 24};

unsigned h1pal_keymap_normalize(unsigned key)
{
    /* These matrix IDs share the same V1.41 game scancode. */
    if (key == 26) key = 40;
    if (key == 28) key = 35;
    if (key == 39) key = 25;
    return key >= 1 && key <= 40 ? key : 0;
}
unsigned h1pal_keymap_get(unsigned action)
{
    return action < H1PAL_KEY_COUNT ? bindings[action] : 0;
}
unsigned h1pal_keymap_default(unsigned action)
{
    return action < H1PAL_KEY_COUNT ? defaults[action] : 0;
}
unsigned h1pal_keymap_action(unsigned key, int fixed)
{
    key = h1pal_keymap_normalize(key);
    for (unsigned i = 0; key && i < H1PAL_KEY_COUNT; ++i)
        if (key == (fixed ? defaults[i] : bindings[i])) return 1u << i;
    return 0;
}
static int valid(const unsigned *keys)
{
    for (unsigned i = 0; i < H1PAL_KEY_COUNT; ++i) {
        if (!keys[i] || h1pal_keymap_normalize(keys[i]) != keys[i]) return 0;
        for (unsigned j = 0; j < i; ++j) if (keys[j] == keys[i]) return 0;
    }
    return 1;
}
void h1pal_keymap_load(void)
{
    char header[32], line[96], extra;
    unsigned keys[H1PAL_KEY_COUNT];
    memcpy(bindings, defaults, sizeof(bindings));
    FILE *f = h1pal_fopen_data("h1keys.cfg", "rb");
    if (!f) return;
    int ok = fgets(header, sizeof(header), f) &&
        strcmp(header, "H1PAL-KEYS 1\n") == 0 && fgets(line, sizeof(line), f) &&
        sscanf(line, "%u %u %u %u %u %u %c", &keys[0], &keys[1], &keys[2],
               &keys[3], &keys[4], &keys[5], &extra) == H1PAL_KEY_COUNT;
    fclose(f);
    if (ok && valid(keys)) memcpy(bindings, keys, sizeof(bindings));
}
static int save(const unsigned *keys)
{
    char text[96];
    int length = snprintf(text, sizeof(text), "H1PAL-KEYS 1\n%u %u %u %u %u %u\n",
        keys[0], keys[1], keys[2], keys[3], keys[4], keys[5]);
    FILE *f = h1pal_fopen_data("h1keys.cfg", "wb");
    if (!f) return 0;
    int ok = fwrite(text, 1, length, f) == (unsigned)length;
    if (fclose(f) != 0) ok = 0;
    if (ok) memcpy(bindings, keys, sizeof(bindings));
    return ok;
}
int h1pal_keymap_assign(unsigned action, unsigned key)
{
    unsigned keys[H1PAL_KEY_COUNT];
    key = h1pal_keymap_normalize(key);
    if (action >= H1PAL_KEY_COUNT || !key) return 0;
    memcpy(keys, bindings, sizeof(keys));
    for (unsigned i = 0; i < H1PAL_KEY_COUNT; ++i)
        if (i != action && keys[i] == key) keys[i] = keys[action];
    keys[action] = key;
    return save(keys);
}
int h1pal_keymap_restore(void) { return save(defaults); }
