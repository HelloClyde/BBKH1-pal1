/* In-game settings use PAL's own border sprites, font and palette.
 * GPL-3.0-or-later. */
#include "main.h"
#include "keymap.h"
#include "platform.h"
#include "wide_scene.h"

static const WCHAR *actions[H1PAL_KEY_COUNT] = {
    L"向上", L"向下", L"向左", L"向右", L"确定", L"取消"
};
static const WCHAR *key_names[41] = {
    L"", L"Q", L"W", L"E", L"R", L"T", L"Y", L"U", L"A", L"S", L"D", L"F",
    L"G", L"H", L"J", L"上翻", L"Z", L"X", L"C", L"V", L"B", L"N", L"下翻",
    L"空格", L"跳出", L"输入", L"左键", L"下键", L"右键", L"I", L"O", L"P",
    L"K", L"L", L"符号", L"右键", L"M", L"上键", L"删除", L"输入", L"左键"
};

static void text(const WCHAR *value, int x, int y, BYTE color)
{
    PAL_DrawText(value, PAL_XY(x, y), color, TRUE, FALSE, FALSE);
}
static void reset_input(void)
{
    h1pal_platform_wait_input_release();
    SDL_H1ResetInputState();
    PAL_ClearKeyState();
    g_InputState.dir = g_InputState.prevdir = kDirUnknown;
}
static SDL_Surface *backup(void)
{
    SDL_Surface *s = SDL_CreateRGBSurface(0, 320, 200, 8, 0, 0, 0, 0);
    if (s) SDL_BlitSurface(gpScreen, NULL, s, NULL);
    return s;
}
static void restore(SDL_Surface *s)
{
    SDL_BlitSurface(s, NULL, gpScreen, NULL);
}
static void panel(SDL_Surface *s, const WCHAR *title)
{
    restore(s);
    PAL_CreateBox(PAL_XY(0, 0), 9, 17, 0, FALSE);
    text(title, 128, 10, MENUITEM_COLOR_CONFIRMED);
}
static int wait_key(void)
{
    PAL_ProcessEvent();
    unsigned key = g_InputState.dwKeyPress;
    PAL_ClearKeyState();
    return key;
}
void H1PAL_KeymapMenu(void)
{
    SDL_Surface *s = backup();
    if (!s) return;
    unsigned selected = 0;
    int capturing = 0, dirty = 1;
    BYTE color = 0;
    const WCHAR *message = L"方向选择 输入改键 跳出返回";
    h1pal_platform_settings_input(1);
    reset_input();
    for (;;) {
        BYTE next_color = MENUITEM_COLOR_SELECTED;
        if (dirty || color != next_color) {
            color = next_color; dirty = 0;
            panel(s, L"按键映射");
            for (unsigned i = 0; i < H1PAL_KEY_COUNT; ++i) {
                BYTE c = selected == i ? color : MENUITEM_COLOR;
                int y = 35 + 19 * i;
                text(actions[i], 48, y, c);
                text(capturing && selected == i ? L"等待按键" : key_names[h1pal_keymap_get(i)], 176, y, c);
                if (selected == i) h1pal_ui_cursor(gpScreen, 48, y);
            }
            text(L"恢复默认", 48, 155, selected == 6 ? color : MENUITEM_COLOR);
            text(L"返回", 224, 155, selected == 7 ? color : MENUITEM_COLOR);
            if (selected >= 6) h1pal_ui_cursor(gpScreen, selected == 6 ? 48 : 224, 155);
            text(message, 32, 178, MENUITEM_COLOR);
            VIDEO_UpdateScreen(NULL);
        }
        unsigned keys = wait_key();
        if (capturing) {
            unsigned key = h1pal_platform_take_capture_key();
            if (key) {
                h1pal_platform_capture_keys(0);
                capturing = 0;
                if (key == 24) message = L"已取消改键";
                else message = h1pal_keymap_assign(selected, key) ? L"已保存，同键自动交换" : L"保存失败，请重试";
                reset_input(); dirty = 1;
            }
        } else if (keys & kKeyMenu) break;
        else if (keys & (kKeyUp | kKeyLeft)) { selected = (selected + 7) % 8; dirty = 1; }
        else if (keys & (kKeyDown | kKeyRight)) { selected = (selected + 1) % 8; dirty = 1; }
        else if (keys & kKeySearch) {
            if (selected == 7) break;
            if (selected == 6) message = h1pal_keymap_restore() ? L"已恢复默认并保存" : L"保存失败，请重试";
            else {
                reset_input();
                h1pal_platform_capture_keys(1);
                capturing = 1; message = L"请按新键，跳出取消";
            }
            dirty = 1;
        }
        SDL_Delay(10);
    }
    h1pal_platform_capture_keys(0);
    reset_input();
    h1pal_platform_settings_input(0);
    SDL_H1ResetInputState(); PAL_ClearKeyState();
    restore(s); SDL_FreeSurface(s); VIDEO_UpdateScreen(NULL);
}
