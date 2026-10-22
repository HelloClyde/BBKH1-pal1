/* Native H1/Y100 V1.41 display, clock and input. GPL-3.0-or-later. */
#include "platform.h"
#include "h1_sdk.h"
#include "game_input.h"
#include "touch.h"
#include "app.h"
#include "pal_config.h"
#include "wide_scene.h"
#include "keymap.h"
#include "scaler.h"
#include <stdio.h>
#include <string.h>
static int opened,timer,closing;
static volatile uint32_t *lcd;
static unsigned sampled,latched,combo_started;
static int combo;
static int settings_input,capturing_keys;
static unsigned captured_key;
static int touch_active,touch_x,touch_y,touch_last_x,touch_last_y,touch_moved;
static unsigned touch_started,tap_time;
static int tap_pending,tap_x,tap_y;
/* A 360x204 map scales uniformly by 4/3 to 480x272. Legacy fixed pictures
 * and AVI keep their aspect ratio. Display geometry has no keyboard toggle. */
static unsigned width=435,height=272,left=22,top=0;
static unsigned logical_width=320,logical_height=200;
static int extended_map,map_full;
static uint16_t xmap[480],ymap[272];
static uint16_t movie_xmap[480],movie_ymap[272];
static unsigned movie_w,movie_h,movie_display_w,movie_display_h;
static void *gui(unsigned o){return h1_runtime_entry(h1_runtime_table(H1_RUNTIME_GUI_TABLE_SLOT),o);}
static int down(unsigned k){return h1_game_code_down(h1_game_key_code(k));}
static void geometry(void){
 map_full=extended_map;
 logical_width=map_full?H1PAL_MAP_WIDTH:320;logical_height=map_full?H1PAL_MAP_HEIGHT:200;
 width=map_full?480:435;height=272;left=(480-width)/2;top=0;
 for(unsigned x=0;x<width;++x)xmap[x]=x*logical_width/width;
 for(unsigned y=0;y<height;++y)ymap[y]=y*logical_height/height;
 if(lcd)for(unsigned i=0;i<480*272;++i)lcd[i]=0;
}
int h1pal_platform_open(void){
 if(opened)return 1;
 typedef int(*open_fn)(void);typedef volatile uint32_t*(*buffer_fn)(uint16_t*,void*);
 open_fn fn=(open_fn)gui(0x84c);if(!fn||!fn())return 0;opened=1;
 uint16_t info[6]={0};buffer_fn get=(buffer_fn)gui(0x8f4);lcd=get?get(info,0):0;
 if(!lcd||info[1]!=480||info[2]!=272||info[3]!=1920||info[5]!=32){h1pal_stats.error=11;h1pal_platform_close();return 0;}
 h1_timer_start();timer=1;geometry();h1pal_log("VIDEO 480x272 stride=1920 bpp=32 lcd=%p",(void*)lcd);return 1;
}
void h1pal_platform_close(void){
 h1pal_scale_shutdown();
 if(timer){h1_timer_stop();timer=0;}
 if(opened){typedef int(*fn)(void);fn close=(fn)gui(0x850);if(close)close();opened=0;}lcd=0;
}
Uint32 h1pal_platform_ticks(void){return timer?h1_timer_read_ms():0;}
void h1pal_platform_delay(Uint32 ms){unsigned start=h1pal_platform_ticks();while(timer&&(unsigned)(h1pal_platform_ticks()-start)<ms)h1pal_platform_pump();}
void h1pal_platform_present(const SDL_Surface *s){
 if(!lcd||!s||!s->pixels||!s->format||!s->format->palette||s->w!=320||s->h!=200)return;
 const Uint8 *wide=h1pal_scene_pixels(s);
 if(extended_map!=!!wide){extended_map=!!wide;geometry();}
 uint32_t palette[256];for(unsigned i=0;i<256;++i){SDL_Color c=s->format->palette->colors[i];palette[i]=(c.r<<16)|(c.g<<8)|c.b;}
 SDL_H1AudioPump();
 unsigned started=h1pal_platform_ticks();
 h1pal_scale_present(s,wide,palette,lcd,width,height,left);
 unsigned elapsed=h1pal_platform_ticks()-started;
 ++h1pal_scale_frames;h1pal_scale_total_ms+=elapsed;if(elapsed>h1pal_scale_max_ms)h1pal_scale_max_ms=elapsed;
 ++h1pal_stats.frames;SDL_H1AudioPump();
}
void h1pal_platform_present_rgb555(const Uint16 *pixels,int w,int h,int pitch){
 if(!lcd||!pixels||w<1||h<1||pitch<w)return;SDL_H1AudioPump();
 if(extended_map){extended_map=0;geometry();}
 if(movie_w!=(unsigned)w||movie_h!=(unsigned)h||movie_display_w!=width||movie_display_h!=height){
  movie_w=w;movie_h=h;movie_display_w=width;movie_display_h=height;
  for(unsigned x=0;x<width;++x)movie_xmap[x]=x*(unsigned)w/width;
  for(unsigned y=0;y<height;++y)movie_ymap[y]=y*(unsigned)h/height;
 }
 for(unsigned y=0;y<height;++y){const uint16_t *in=pixels+movie_ymap[y]*pitch;volatile uint32_t *out=lcd+(top+y)*480+left;
 for(unsigned x=0;x<width;++x){unsigned c=in[movie_xmap[x]],r=(c>>10)&31,g=(c>>5)&31,b=c&31;out[x]=(((r<<3)|(r>>2))<<16)|(((g<<3)|(g>>2))<<8)|(b<<3)|(b>>2);}}
 ++h1pal_stats.frames;SDL_H1AudioPump();
}
static int absolute(int n){return n<0?-n:n;}
static void touch_event(int event){
 int x,y;if(event!=11&&!touch_active)return;
 if(h1_touch_position(&x,&y)){touch_last_x=x;touch_last_y=y;}else if(event==11)return;
 x=touch_last_x;y=touch_last_y;unsigned now=h1pal_platform_ticks();
 if(event==11){touch_active=1;touch_x=x;touch_y=y;touch_started=now;touch_moved=0;}
 else{if(absolute(x-touch_x)>18||absolute(y-touch_y)>18)touch_moved=1;
 if(event==8){if(!touch_moved&&now-touch_started<=750&&x>=(int)left&&y>=(int)top&&x<(int)(left+width)&&y<(int)(top+height)){
 tap_x=(x-left)*(int)logical_width/(int)width-(map_full?H1PAL_MAP_LEFT:0);
 tap_y=(y-top)*(int)logical_height/(int)height-(map_full?H1PAL_MAP_TOP:0);tap_pending=1;tap_time=now;++h1pal_stats.taps;}touch_active=0;}}
}
void h1pal_platform_pump(void){
 if(!opened)return;
 for(unsigned i=0;i<32;++i){int event=-1,value=-1;h1_event_fetch(&event,&value);if(event==-1&&value==-1)break;
 if(event==11||event==12||event==8)touch_event(event);
 if(event==H1_EVENT_KEY_DOWN){++h1pal_stats.keys;if(value==H1_KEY_BACK)closing=1;
 if(capturing_keys&&!captured_key)captured_key=h1pal_keymap_normalize(value);
 latched|=h1pal_keymap_action(value,settings_input);}}
 if(touch_active)touch_event(12);
 unsigned keys=0;
 for(unsigned i=0;i<H1PAL_KEY_COUNT;++i)if(down(settings_input?h1pal_keymap_default(i):h1pal_keymap_get(i)))keys|=1u<<i;
 if(capturing_keys&&!captured_key)for(unsigned key=1;key<=40;++key)if(h1pal_keymap_normalize(key)==key&&down(key)){captured_key=key;break;}
 latched|=keys&~sampled;sampled=keys;
 /* The emergency exit remains tied to physical Enter+Escape, regardless of mappings. */
 if(down(H1_KEY_ENTER)&&down(H1_KEY_ESCAPE)){if(!combo){combo=1;combo_started=h1pal_platform_ticks();}else if(h1pal_platform_ticks()-combo_started>=1500)closing=1;}else combo=0;
}
unsigned h1pal_platform_keys(void){h1pal_platform_pump();unsigned keys=sampled|latched;latched=0;return keys;}
int h1pal_platform_detached(void){return closing;}
int h1pal_platform_take_tap(int *x,int *y){if(!tap_pending)return 0;tap_pending=0;if(h1pal_platform_ticks()-tap_time>500)return 0;*x=tap_x;*y=tap_y;return 1;}
void h1pal_platform_wait_action_release(void){
 unsigned quiet=h1pal_platform_ticks();
 do{h1pal_platform_pump();SDL_H1AudioPump();if(sampled&48)quiet=h1pal_platform_ticks();}
 while(!closing&&h1pal_platform_ticks()-quiet<120);
 latched=0;
}
void h1pal_platform_settings_input(int enabled){settings_input=enabled;sampled=latched=0;tap_pending=0;touch_active=0;}
void h1pal_platform_capture_keys(int enabled){capturing_keys=enabled;captured_key=0;}
unsigned h1pal_platform_take_capture_key(void){unsigned key=captured_key;captured_key=0;return key;}
void h1pal_platform_wait_input_release(void){
 unsigned quiet=h1pal_platform_ticks();
 do{h1pal_platform_pump();SDL_H1AudioPump();
  for(unsigned key=1;key<=40;++key)if(h1pal_keymap_normalize(key)==key&&down(key)){quiet=h1pal_platform_ticks();break;}
 }while(!closing&&h1pal_platform_ticks()-quiet<120);
 sampled=latched=captured_key=0;
}
void H1PAL_FatalOutput(const char *message){
 h1pal_stats.error=1;h1pal_log("FATAL %s",message?message:"");h1pal_platform_close();
 h1_message_box(0,"\xCE\xDE\xB7\xA8\xB6\xC1\xC8\xA1\xCF\xC9\xBD\xA3\xD7\xCA\xD4\xB4\xA1\xA3\nA:" H1PAL_DATA_DIRECTORY "PAL9588.PAK\nB:" H1PAL_DATA_DIRECTORY "PAL9588.PAK","\xCF\xC9\xBD\xA3 1",0);
}
