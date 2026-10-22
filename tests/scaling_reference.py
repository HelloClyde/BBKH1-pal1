"""Slow image-space reference: nearest 2x image, then centred bilinear lookup."""
from fractions import Fraction
from math import floor

def axis(index,source,target,offset=0):
    position=Fraction((2*(index+offset)+1)*source,target)-Fraction(1,2)
    first=floor(position);weight=position-first
    return (max(0,min(source-1,first//2)),max(0,min(source-1,(first+1)//2)),weight)

def blend(a,b,w):
    return tuple(floor(x*(1-w)+y*w+Fraction(1,2)) for x,y in zip(a,b))

def sample(data,w,h,palette,x,y,target_w=480,target_h=272,y_offset=0):
    a,b,wx=axis(x,w,target_w);c,d,wy=axis(y,h,target_h,y_offset)
    top=blend(palette[data[c*w+a]],palette[data[c*w+b]],wx)
    bottom=blend(palette[data[d*w+a]],palette[data[d*w+b]],wx)
    return blend(top,bottom,wy)

def close(actual,expected,tolerance=2):
    channels=((actual>>16)&255,(actual>>8)&255,actual&255)
    return all(abs(a-b)<=tolerance for a,b in zip(channels,expected))
