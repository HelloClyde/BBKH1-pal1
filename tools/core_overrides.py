"""Small, checked H1 overrides generated from the pristine pinned SDLPAL tree.

Keep the dependency checkout unchanged. Replacements fail if the upstream
contexts change; generated C retains the original copyright/license headers.
"""
def generate(core, directory):
    directory.mkdir(parents=True, exist_ok=True)
    output = {}
    for name in ('scene.c', 'rngplay.c', 'battle.c', 'video.c', 'uigame.c', 'magicmenu.c', 'itemmenu.c', 'aviplay.c', 'text.c'):
        text = (core / name).read_text(encoding='utf-8')
        def replace(old, new):
            nonlocal text
            assert text.count(old) == 1, (name, old, text.count(old))
            text = text.replace(old, new)
        if name == 'text.c':
            replace(r'L"\x8FD4\x56DE\x8A2D\x5B9A"', r'L"\x6309\x9375\x6620\x5C04"')
            replace(r'L"\x8FD4\x56DE\x8BBE\x7F6E"', r'L"\x6309\x952E\x6620\x5C04"')
        elif name == 'aviplay.c':
            replace('#include "palcfg.h"', '#include "palcfg.h"\n#include "h264_video.h"\n#define H1PAL_VIDS_H264 0x34363248u')
            replace('BOOL          fInterleaved;', 'BOOL          fInterleaved;\n    uint32_t h1codec;')
            replace('(streamHeader.fccHandler != VIDS_MSVC && streamHeader.fccHandler != VIDS_msvc)',
                    '(streamHeader.fccHandler != VIDS_MSVC && streamHeader.fccHandler != VIDS_msvc && streamHeader.fccHandler != H1PAL_VIDS_H264)')
            replace('if (bih.biBitCount != 16)', 'avi->h1codec = streamHeader.fccHandler;\n                    if (avi->h1codec != H1PAL_VIDS_H264 && bih.biBitCount != 16)')
            replace('bih.biWidth, bih.biHeight, bih.biBitCount,', 'bih.biWidth, bih.biHeight, 16,')
            replace('chunk->header = hdr.chunk;', 'chunk->header = hdr.chunk;\n            if (hdr.length & 1u) fseek(fp, 1, SEEK_CUR);')
            replace('fseek(fp, pos += hdr.length, SEEK_SET);', 'fseek(fp, pos += hdr.length + (hdr.length & 1u), SEEK_SET);')
            # Preserve the AVI timeline instead of adding each timer overshoot
            # to the next frame, which slowly lets video fall behind PCM.
            replace('dwFrameStartTime = SDL_GetTicks();', 'dwFrameStartTime = dwNextFrameTime;')
            replace('PAL_RenderAVIFrameToSurface(avi->surface, chunk);',
                    'if (avi->h1codec == H1PAL_VIDS_H264) {\n'
                    '                if (!h1pal_h264_decode(avi->surface, chunk->data, chunk->header.length)) { fEndPlay = TRUE; break; }\n'
                    '            } else PAL_RenderAVIFrameToSurface(avi->surface, chunk);')
        else:
            replace('#include "main.h"', '#include "main.h"\n#include "wide_scene.h"')
        if name in ('aviplay.c', 'text.c'):
            pass
        elif name == 'scene.c':
            replace('if (x >= 320 ||', 'if (x >= gpScreen->w ||')
            replace('if (vy >= 200 ||', 'if (vy >= gpScreen->h ||')
            replace('BYTE                 buf[320];', 'BYTE                 buf[H1PAL_MAP_WIDTH];')
            replace('wave[i] = a * gpGlobals->wScreenWave / 256;',
                    'wave[i] = (a * gpGlobals->wScreenWave / 256) % lpSurface->w;')
            replace('wave[i + 16] = 320 - wave[i];', 'wave[i + 16] = lpSurface->w - wave[i];')
            replace('for (i = 0; i < 200; i++)', 'for (i = 0; i < lpSurface->h; i++)')
            replace('memmove(p, &p[b], 320 - b);', 'memmove(p, &p[b], lpSurface->w - b);')
            replace('memcpy(&p[320 - b], buf, b);', 'memcpy(&p[lpSurface->w - b], buf, b);')
            replace('static SDL_Rect         rect = {0, 0, 320, 200};',
                    'SDL_Rect rect;\n\n   h1pal_scene_begin();\n   rect.w = gpScreen->w;\n   rect.h = gpScreen->h;')
            replace('   PAL_SceneDrawSprites();', '   PAL_SceneDrawSprites();\n   h1pal_scene_end();')
        elif name == 'rngplay.c':
            replace('   int                   ptr         = 0;',
                    '   h1pal_scene_clear(lpDstSurface);\n   int                   ptr         = 0;')
        elif name == 'battle.c':
            replace('   PAL_FBPBlitToSurface(buf, g_Battle.lpBackground);',
                    '   PAL_FBPBlitToSurface(buf, g_Battle.lpBackground);\n   h1pal_battle_load_background(g_Battle.lpBackground);')
            start = text.index('   pSrc = g_Battle.lpBackground->pixels;')
            end = text.index('   PAL_ApplyWave(g_Battle.lpSceneBuf);') + len('   PAL_ApplyWave(g_Battle.lpSceneBuf);')
            replace(text[start:end], '   h1pal_battle_make_background();')
            replace('         // Draw the backup buffer to the screen\n         //',
                    '         // Draw the backup buffer to the screen\n         //\n         h1pal_scene_fade(g_Battle.lpSceneBuf, gpScreenBak, rgIndex[j], i);')
        elif name == 'video.c':
            replace('      // Draw the backup buffer to the screen\n      //',
                    '      // Draw the backup buffer to the screen\n      //\n      h1pal_scene_switch(gpScreen, gpScreenBak, rgIndex[i]);')
            replace('            ((LPBYTE)(gpScreenBak->pixels))[k] = ((a & 0xF0) | (b & 0x0F));\n         }',
                    '            ((LPBYTE)(gpScreenBak->pixels))[k] = ((a & 0xF0) | (b & 0x0F));\n         }\n         h1pal_scene_fade(gpScreen, gpScreenBak, rgIndex[j], i);')
        elif name == 'uigame.c':
            replace('#include "main.h"', '#include "main.h"\n#include "keymap.h"')
            replace('      { 5,      SYSMENU_LABEL_QUIT,          TRUE,     PAL_XY(53, 72 + 72) },',
                    '      { 5,      SYSMENU_LABEL_LAUNCHSETTING, TRUE,     PAL_XY(53, 72 + 72) },\n'
                    '      { 6,      SYSMENU_LABEL_QUIT,          TRUE,     PAL_XY(53, 72 + 90) },')
            replace('      { 6,      SYSMENU_LABEL_BATTLEMODE,    TRUE,     PAL_XY(53, 72 + 90) },',
                    '      { 7,      SYSMENU_LABEL_BATTLEMODE,    TRUE,     PAL_XY(53, 72 + 108) },')
            replace('   case 6:\n      //\n      // Battle Mode', '   case 7:\n      //\n      // Battle Mode')
            replace('   case 5:\n      //\n      // Quit',
                    '   case 5:\n      H1PAL_KeymapMenu();\n      break;\n\n   case 6:\n      //\n      // Quit')
            replace('   PAL_FBPBlitToSurface(buf, gpScreen);',
                    '   PAL_FBPBlitToSurface(buf, gpScreen);\n   h1pal_ui_background(gpScreen, 1);')
            old = '      PAL_FBPBlitToSurface(bufBackground, gpScreen);'
            assert text.count(old) == 2, (name, old)
            text = text.replace(old, old + '\n      h1pal_ui_background(gpScreen, 0);')
            replace('         int index = &gConfig.ScreenLayout.RoleEquipNames[i] - gConfig.ScreenLayoutArray;',
                    '         if (!gConfig.fUseCustomScreenLayout) offset = h1pal_ui_equipment_offset(w, i);\n'
                    '         int index = &gConfig.ScreenLayout.RoleEquipNames[i] - gConfig.ScreenLayoutArray;')
            text += '\n#if H1PAL_REGRESSION\nvoid H1PAL_TestInventoryMenu(void) { PAL_InventoryMenu(); }\n#endif\n'
        else:
            if name == 'magicmenu.c':
                old = ('            PAL_RLEBlitToSurface(PAL_SpriteGetFrame(gpSpriteUI, SPRITENUM_CURSOR),\n'
                       '               gpScreen, PAL_XY(35 + iCursorXOffset + k * iItemTextWidth, 64 + j * 18 + iBoxYOffset));')
                new = '            h1pal_ui_cursor(gpScreen, 35 + k * iItemTextWidth, 54 + j * 18 + iBoxYOffset);'
            else:
                old = ('            PAL_RLEBlitToSurface(PAL_SpriteGetFrame(gpSpriteUI, SPRITENUM_CURSOR),\n'
                       '               gpScreen, PAL_XY(15 + iCursorXOffset + k * iItemTextWidth, 22 + j * 18));')
                new = '            h1pal_ui_cursor(gpScreen, 15 + k * iItemTextWidth, 12 + j * 18);'
            replace(old, new)
        path = directory / name
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            path.write_text(text, encoding='utf-8')
        output[name] = path
    return output
