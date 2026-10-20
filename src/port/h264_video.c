/* H.264 Baseline AVI frames; GPL-3.0-or-later, decoder Apache-2.0/MIT. */
#include "h264_video.h"
#include "h264bsd_decoder.h"
#include "platform.h"
#include "app.h"
#include <stdlib.h>

static storage_t *decoder;
static int failed;
unsigned h1pal_h264_frames, h1pal_h264_max_ms,h1pal_h264_total_ms;
static int y_table[256],r_table[256],g_u[256],g_v[256],b_table[256];
static unsigned char clip5[1024];
static int tables_ready;

void h1pal_h264_close(void)
{
    if (decoder) { h264bsdShutdown(decoder); free(decoder); decoder=0; }
}
void h1pal_h264_reset(void)
{
    h1pal_h264_close(); failed=0;
    h1pal_h264_frames=h1pal_h264_max_ms=h1pal_h264_total_ms=0;
}
int h1pal_h264_failed(void) { return failed; }
static void make_tables(void)
{
    if(tables_ready)return;
    for(int i=0;i<256;++i){
        y_table[i]=298*(i-16)+128;r_table[i]=409*(i-128);
        g_u[i]=-100*(i-128);g_v[i]=-208*(i-128);b_table[i]=516*(i-128);
    }
    for(int i=0;i<1024;++i){int c=i-384;clip5[i]=(unsigned char)(c<0?0:(c>255?31:c>>3));}
    tables_ready=1;
}
static Uint16 pixel(int luma,int red,int green,int blue)
{
    return (Uint16)((clip5[((luma+red)>>8)+384]<<10)|
        (clip5[((luma+green)>>8)+384]<<5)|clip5[((luma+blue)>>8)+384]);
}

static int draw(SDL_Surface *surface, const unsigned char *picture)
{
    u32 crop,left,w,top,h;
    unsigned stride=h264bsdPicWidth(decoder)*16, rows=h264bsdPicHeight(decoder)*16;
    h264bsdCroppingParams(decoder,&crop,&left,&w,&top,&h);
    if(!crop){left=top=0;w=stride;h=rows;}
    if(w!=(unsigned)surface->w || h!=(unsigned)surface->h || left+w>stride || top+h>rows || (w|left)&1)return 0;
    const unsigned char *u=picture+stride*rows, *v=u+stride*rows/4;
    for(unsigned y=0;y<h;++y){
        Uint16 *out=(Uint16 *)((unsigned char *)surface->pixels+y*surface->pitch);
        const unsigned char *luma=picture+(top+y)*stride+left;
        unsigned chroma=(top+y)/2*(stride/2)+left/2;
        for(unsigned x=0;x<w;x+=2,++chroma){
            unsigned cb=u[chroma],cr=v[chroma];
            int red=r_table[cr],green=g_u[cb]+g_v[cr],blue=b_table[cb];
            out[x]=pixel(y_table[luma[x]],red,green,blue);
            out[x+1]=pixel(y_table[luma[x+1]],red,green,blue);
        }
    }
    return 1;
}
int h1pal_h264_decode(SDL_Surface *surface, unsigned char *data, unsigned length)
{
    unsigned started=h1pal_platform_ticks(),pictures=0,stalls=0;
    if(failed || !surface || surface->w<1 || surface->h<1 || surface->w>320 || surface->h>240)return 0;
    if(!decoder){
        make_tables();
        decoder=(storage_t *)calloc(1,sizeof(*decoder));
        if(!decoder || h264bsdInit(decoder,1)!=0)goto error;
    }
    while(length){
        u32 consumed=0,id=0,idr=0,errors=0;
        u32 result=h264bsdDecode(decoder,data,length,h1pal_h264_frames,&consumed);
        if(consumed>length || result>=H264BSD_ERROR)goto error;
        if(result==H264BSD_HDRS_RDY){
            if(h264bsdProfile(decoder)!=66 || h264bsdPicWidth(decoder)*16>320 || h264bsdPicHeight(decoder)*16>240)goto error;
        }
        if(result==H264BSD_PIC_RDY){
            unsigned char *picture=h264bsdNextOutputPicture(decoder,&id,&idr,&errors);
            if(!picture || errors || !draw(surface,picture))goto error;
            ++pictures;
        }
        if(!consumed){if(++stalls>8)goto error;}else stalls=0;
        data+=consumed;length-=consumed;
    }
    if(pictures!=1)goto error;
    ++h1pal_h264_frames;
    unsigned elapsed=h1pal_platform_ticks()-started;
    h1pal_h264_total_ms+=elapsed;
    if(elapsed>h1pal_h264_max_ms)h1pal_h264_max_ms=elapsed;
    return 1;
error:
    failed=1;h1pal_log("H264_DECODE_FAILED frame=%u",h1pal_h264_frames);return 0;
}
