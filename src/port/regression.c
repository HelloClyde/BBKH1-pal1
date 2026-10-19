#if H1PAL_REGRESSION
int testmain(int argc,char **argv) { (void)argc;(void)argv;extern void PAL_GameMain(void);PAL_GameMain();return 0; }
#include "main.h"
#include "pal_config.h"
#include "platform.h"
#include "regression.h"
#include "wide_scene.h"

#include <stdio.h>
#include <string.h>

#define SAVE_MARKER   PAL_H1_DATA_PATH "PORTTEST.SAVE"
#define BATTLE_MARKER PAL_H1_DATA_PATH "PORTTEST.BATTLE"
#define VIDEO_MARKER  PAL_H1_DATA_PATH "PORTTEST.VIDEO"
#define SOUND_MARKER  PAL_H1_DATA_PATH "PORTTEST.SOUND"
#define VIEW_MARKER   PAL_H1_DATA_PATH "PORTTEST.VIEW"
#define INTERACTIVE_MARKER PAL_H1_DATA_PATH "PORTTEST.INTERACTIVE"
#define UI_MARKER PAL_H1_DATA_PATH "PORTTEST.UI"
#define TEST_LOG      PAL_H1_DATA_PATH "PORTTEST.LOG"
#define SAVE_EXPECT   PAL_H1_DATA_PATH "PORTTEST.EXPECT"

#define SAVE_EXPECT_MAGIC 0x31545350u

#define BATTLE_TEST_FIELD 2u
#define BATTLE_TEST_MUSIC 37u

typedef struct h1pal_save_expect
{
    DWORD magic;
    WORD scene;
    WORD hp;
    DWORD cash;
} h1pal_save_expect_t;

enum
{
    REGRESSION_NONE,
    REGRESSION_SAVE,
    REGRESSION_BATTLE,
    REGRESSION_VIDEO,
    REGRESSION_SOUND
};

static int g_regression_mode;
static int g_regression_interactive;

extern VOID H1PAL_InternalGameMain(VOID);
extern unsigned h1pal_avi_last_frame_count(void);
extern unsigned h1pal_avi_last_exit_keys(void);

static int file_exists(const char *path)
{
    FILE *file = fopen(path, "rb");
    if (!file) return 0;
    fclose(file);
    return 1;
}

int h1pal_regression_active(void)
{
    return file_exists(SAVE_MARKER) || file_exists(BATTLE_MARKER) ||
        file_exists(VIDEO_MARKER) || file_exists(SOUND_MARKER) || file_exists(VIEW_MARKER) || file_exists(UI_MARKER);
}

int h1pal_regression_auto_battle(void)
{
    return g_regression_mode == REGRESSION_BATTLE && !g_regression_interactive && gpGlobals &&
        gpGlobals->fInBattle &&
        g_Battle.BattleResult == kBattleResultOnGoing;
}

static void reset_log(const char *heading)
{
    FILE *file = fopen(TEST_LOG, "wb");
    if (!file) return;
    fputs(heading, file);
    fputs("\r\n", file);
    fclose(file);
}

static void append_log(const char *line)
{
    FILE *file = fopen(TEST_LOG, "ab");
    if (!file) return;
    fputs(line, file);
    fputs("\r\n", file);
    fclose(file);
}

static int saved_file_header_valid(void)
{
    unsigned char header[2];
    FILE *file = fopen(PAL_H1_DATA_PATH "2.rpg", "rb");
    size_t count;
    long length;
    if (!file) return 0;
    count = fread(header, 1, sizeof(header), file);
    fseek(file, 0, SEEK_END);
    length = ftell(file);
    fclose(file);
    return count == sizeof(header) && header[0] == 0x34u &&
        header[1] == 0x12u && length > 100000;
}

static int read_save_expect(h1pal_save_expect_t *expect)
{
    FILE *file = fopen(SAVE_EXPECT, "rb");
    size_t count;
    if (!file) return 0;
    count = fread(expect, 1, sizeof(*expect), file);
    fclose(file);
    return count == sizeof(*expect) && expect->magic == SAVE_EXPECT_MAGIC;
}

static int write_save_expect(const h1pal_save_expect_t *expect)
{
    FILE *file = fopen(SAVE_EXPECT, "wb");
    size_t count;
    if (!file) return 0;
    count = fwrite(expect, 1, sizeof(*expect), file);
    fclose(file);
    return count == sizeof(*expect);
}

static void run_save_regression(void)
{
    h1pal_save_expect_t expect;
    int passed;

    if (read_save_expect(&expect)) {
        append_log("RELOAD START");
        gpGlobals->fInMainGame = TRUE;
        PAL_InitGameData(2);
        passed = saved_file_header_valid() &&
            gpGlobals->wNumScene == expect.scene &&
            gpGlobals->dwCash == expect.cash &&
            gpGlobals->g.PlayerRoles.rgwHP[0] == expect.hp;
        append_log(passed ? "RELOAD PASS" : "RELOAD FAIL");
        PAL_Shutdown(passed ? 0 : 2);
    }

    reset_log("SAVE START");
    gpGlobals->fInMainGame = TRUE;
    PAL_InitGameData(1);
    expect.magic = SAVE_EXPECT_MAGIC;
    expect.scene = gpGlobals->wNumScene;
    expect.cash = gpGlobals->dwCash;
    expect.hp = gpGlobals->g.PlayerRoles.rgwHP[0];

    PAL_SaveGame(2, 0x1234u);
    passed = saved_file_header_valid() && write_save_expect(&expect);
    append_log(passed ? "SAVE PASS" : "SAVE FAIL");
    PAL_Shutdown(passed ? 0 : 2);
}

static void run_video_regression(void)
{
    static const char *const movies[] = {
        "3.avi", "4.avi", "5.avi", "6.avi"
    };
    unsigned i;
    int passed = 1;

    reset_log("VIDEO START");
    for (i = 0; i < sizeof(movies) / sizeof(movies[0]); ++i) {
        int played = PAL_PlayAVI(movies[i]);
        unsigned frames = h1pal_avi_last_frame_count();
        unsigned exit_keys = h1pal_avi_last_exit_keys();
        char line[64];
        snprintf(line, sizeof(line), "VIDEO %u FRAMES %u KEYS %u %s",
            i + 3u, frames, exit_keys, played ? "PASS" : "FAIL");
        append_log(line);
        if (!played) {
            passed = 0;
        }
    }
    append_log(passed ? "VIDEO PASS" : "VIDEO FAIL");
    PAL_Shutdown(passed ? 0 : 3);
}

static void run_battle_regression(void)
{
    BATTLERESULT result;

    reset_log("BATTLE START");
    g_regression_interactive = file_exists(INTERACTIVE_MARKER);
    gpGlobals->fInMainGame = TRUE;
    /*
     * Use a deterministic new-game state instead of depending on a loose
     * 1.rpg save.  The default state intentionally leaves the battlefield at
     * FBP chunk 0, which is the player-status background rather than a battle
     * scene; normal gameplay sets both values through scripts before combat.
     */
    PAL_InitGameData(0);
    gpGlobals->wNumBattleField = BATTLE_TEST_FIELD;
    gpGlobals->wNumBattleMusic = BATTLE_TEST_MUSIC;
    PAL_SetPalette(gpGlobals->wNumPalette, gpGlobals->fNightPalette);
    PAL_SetLoadFlags(kLoadScene | kLoadPlayerSprite);
    PAL_LoadResources();
    append_log("BATTLE READY");
    AUDIO_PlayMusic(gpGlobals->wNumBattleMusic, TRUE, 0);
    result = PAL_StartBattle(1, FALSE);
    if (result == kBattleResultWon) append_log("BATTLE WON");
    else if (result == kBattleResultFleed) append_log("BATTLE FLED");
    else append_log("BATTLE OTHER");
    PAL_Shutdown(result == kBattleResultWon ? 0 : 4);
}

static void run_sound_regression(void)
{
    const Uint32 duration = 5000u;
    Uint32 started;
    Uint32 maximum_iteration = 0u;
    unsigned iterations = 0u;
    unsigned key_events = 0u;
    unsigned taps = 0u;
    SDL_Event event;
    char line[96];

    reset_log("SOUND START");
    AUDIO_PlayMusic(0, FALSE, 0);
    /* The six night-watch drum hits before meeting the Sword Master use 93. */
    AUDIO_PlaySound(93);
    started = SDL_GetTicks();
    while ((Uint32)(SDL_GetTicks() - started) < duration) {
        Uint32 before = SDL_GetTicks();
        int x;
        int y;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_KEYDOWN) ++key_events;
        }
        if (h1pal_platform_take_tap(&x, &y)) ++taps;
        SDL_Delay(1u);
        before = SDL_GetTicks() - before;
        if (before > maximum_iteration) maximum_iteration = before;
        ++iterations;
    }
    snprintf(line, sizeof(line),
        "SOUND ITERATIONS %u MAX_MS %u KEYS %u TAPS %u",
        iterations, maximum_iteration, key_events, taps);
    append_log(line);
    append_log((key_events || taps) ? "SOUND INPUT PASS" : "SOUND INPUT NONE");
    PAL_Shutdown(0);
}

/* Host test observes these checkpoints after real engine drawing. */
__attribute__((noinline)) void h1pal_view_checkpoint(unsigned phase)
{
    __asm__ volatile("" : : "r"(phase) : "memory");
}
static void run_view_regression(void)
{
    extern int h1pal_scene_test_legacy;
    PARTY original_party[MAX_PLAYABLE_PLAYER_ROLES];
    PAL_POS original_viewport;
    int i, ok;
    BYTE background[320 * 200] = {0};
    reset_log("VIEW START");
    gpGlobals->fInMainGame = TRUE;
    PAL_InitGameData(1);
    PAL_SetLoadFlags(kLoadScene | kLoadPlayerSprite);
    PAL_LoadResources();
    PAL_UpdatePartyGestures(FALSE);
    gpGlobals->fNeedToFadeIn = FALSE;
    gpGlobals->wScreenWave = gpGlobals->sWaveProgression = 0;
    PAL_SetPalette(gpGlobals->wNumPalette, gpGlobals->fNightPalette);
    original_viewport = gpGlobals->viewport;
    memcpy(original_party, gpGlobals->rgParty, sizeof(original_party));
    PAL_MakeScene(); VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(1);
    ok = gpGlobals->viewport == original_viewport &&
        memcmp(original_party, gpGlobals->rgParty, sizeof(original_party)) == 0;
    append_log(ok ? "VIEW STATE PASS" : "VIEW STATE FAIL");
    /* Native key-state/touch fixtures are supplied by the host test at these
     * checkpoints. Coordinates may be negative relative to the old view. */
    for (i = 0; i < 3; ++i) {
        int x, y;
        int expected_x[] = {339, 319, 319}, expected_y[] = {201, 199, 199};
        h1pal_view_checkpoint(10 + i * 3);
        h1pal_platform_pump();
        h1pal_view_checkpoint(11 + i * 3);
        h1pal_platform_pump();
        ok = ok && h1pal_platform_take_tap(&x, &y) && x == expected_x[i] && y == expected_y[i];
    }
    h1pal_view_checkpoint(19); h1pal_platform_pump();
    h1pal_view_checkpoint(20); h1pal_platform_pump();
    { int x, y; ok = ok && h1pal_platform_take_tap(&x, &y) && x == -20 && y == -2; }
    append_log(ok ? "VIEW TAP PASS" : "VIEW TAP FAIL");
    VIDEO_BackupScreen(gpScreen);
    PAL_FBPBlitToSurface(background, gpScreen);
    VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(2);
    VIDEO_RestoreScreen(gpScreen);
    VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(3);
    { SDL_Rect small = {0, 0, 16, 16};
      VIDEO_UpdateScreen(&small); h1pal_view_checkpoint(21); }
    h1pal_scene_test_legacy = 1;
    PAL_MakeScene(); VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(4);
    h1pal_scene_test_legacy = 0;
    /* An event with its centre outside the old view must still draw in the
     * extra map columns, including its covering tiles and original layering. */
    for (i = gpGlobals->g.rgScene[gpGlobals->wNumScene - 1].wEventObjectIndex;
         i < gpGlobals->g.rgScene[gpGlobals->wNumScene].wEventObjectIndex; ++i) {
        EVENTOBJECT *object = &gpGlobals->g.lprgEventObject[i];
        EVENTOBJECT saved = *object;
        if (!PAL_GetEventObjectSprite(i + 1)) continue;
        object->x = PAL_X(original_viewport) - 4;
        object->y = PAL_Y(original_viewport) + 130;
        object->sState = 1; object->sVanishTime = 0;
        PAL_MakeScene(); VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(5);
        object->sState = kObjStateHidden;
        PAL_MakeScene(); VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(6);
        *object = saved;
        break;
    }
    /* Exercise the generalized 360x204 water/dream effect at its largest
     * legal amplitude; it used to assume exactly 320 bytes per row. */
    gpGlobals->wScreenWave = 255;
    PAL_MakeScene(); VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(7);
    gpGlobals->fInBattle = TRUE;
    VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(8);
    gpGlobals->fInBattle = FALSE;
    VIDEO_ShakeScreen(1, 5);
    VIDEO_UpdateScreen(NULL); h1pal_view_checkpoint(9);
    append_log("VIEW PASS");
    PAL_Shutdown(ok ? 0 : 5);
}

volatile unsigned h1pal_ui_test_stage;
__attribute__((noinline)) void h1pal_ui_checkpoint(unsigned stage)
{
    h1pal_ui_test_stage = stage;
    __asm__ volatile("" : : "r"(stage) : "memory");
}
static void prepare_ui_stage(unsigned stage)
{
    h1pal_ui_test_stage = 0;
    PAL_ClearKeyState();
    PAL_MakeScene(); VIDEO_UpdateScreen(NULL);
    h1pal_ui_checkpoint(stage);
}
static void run_ui_regression(void)
{
    extern VOID H1PAL_TestInventoryMenu(VOID);
    WORD equip = 0, usable = 0, i, role;
    reset_log("UI START");
    h1pal_ui_checkpoint(1);
    PAL_OpeningMenu();
    gpGlobals->fInMainGame = TRUE;
    PAL_InitGameData(1);
    PAL_SetLoadFlags(kLoadScene | kLoadPlayerSprite); PAL_LoadResources();
    PAL_UpdatePartyGestures(FALSE);
    gpGlobals->fNeedToFadeIn = FALSE;
    PAL_SetPalette(gpGlobals->wNumPalette, gpGlobals->fNightPalette);
    role = gpGlobals->rgParty[0].wPlayerRole;
    /* Deterministic menu fixtures only; they are never saved. */
    for (i = OBJECT_ITEM_START; i < OBJECT_ITEM_END; ++i) {
        WORD flags = gpGlobals->g.rgObject[i].item.wFlags;
        if (!equip && (flags & kItemFlagEquipable)) equip = i;
        if (!usable && (flags & kItemFlagUsable)) usable = i;
    }
    PAL_AddItemToInventory(equip, 1); PAL_AddItemToInventory(usable, 3);
    for (i = OBJECT_MAGIC_START; i < OBJECT_MAGIC_END; ++i) {
        if (gpGlobals->g.rgObject[i].magic.wFlags & kMagicFlagUsableOutsideBattle) {
            PAL_AddMagic(role, i); break;
        }
    }
    prepare_ui_stage(2); PAL_PlayerStatus();
    prepare_ui_stage(3); PAL_EquipItemMenu(equip);
    h1pal_ui_test_stage = 0; PAL_DrawOpeningMenuBackground();
    h1pal_ui_checkpoint(4); PAL_SaveSlotMenu(1);
    prepare_ui_stage(5); PAL_InGameMenu();
    prepare_ui_stage(6); H1PAL_TestInventoryMenu();
    prepare_ui_stage(7); PAL_ItemSelectMenu(NULL, kItemFlagUsable);
    prepare_ui_stage(8); PAL_MagicSelectionMenu(role, FALSE, 0);
    prepare_ui_stage(9); PAL_InGameMagicMenu();
    prepare_ui_stage(10); PAL_ItemUseMenu(usable);
    prepare_ui_stage(11); PAL_ConfirmMenu();
    prepare_ui_stage(12); PAL_BuyMenu(0);
    prepare_ui_stage(13); PAL_SellMenu();
    h1pal_ui_test_stage = 0;
    append_log("UI PASS"); PAL_Shutdown(0);
}

VOID PAL_GameMain(VOID)
{
    if (file_exists(UI_MARKER)) run_ui_regression();
    if (file_exists(VIEW_MARKER)) run_view_regression();
    if (file_exists(SAVE_MARKER)) {
        g_regression_mode = REGRESSION_SAVE;
        run_save_regression();
    }
    if (file_exists(VIDEO_MARKER)) {
        g_regression_mode = REGRESSION_VIDEO;
        run_video_regression();
    }
    if (file_exists(BATTLE_MARKER)) {
        g_regression_mode = REGRESSION_BATTLE;
        run_battle_regression();
    }
    if (file_exists(SOUND_MARKER)) {
        g_regression_mode = REGRESSION_SOUND;
        run_sound_regression();
    }
    g_regression_mode = REGRESSION_NONE;
    H1PAL_InternalGameMain();
}

#else
int h1pal_regression_active(void){return 0;}
int h1pal_regression_auto_battle(void){return 0;}
extern void H1PAL_InternalGameMain(void);
void PAL_GameMain(void){H1PAL_InternalGameMain();}
#endif
