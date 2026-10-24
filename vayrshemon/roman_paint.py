"""Roman layer style measured in Translation 1/2.psd, independent of Thimfora.

The PSD styles are expressed at a 500 px em. Blur sizes are mapped to finite
Gaussian support; all masks come from the selected font's unmodified outlines.
This reconstructs the style, not Photoshop's proprietary raster algorithm.
"""
import json
import math
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, shift
from PySide6.QtGui import QImage

PROFILE=json.loads((Path(__file__).resolve().parents[1]/'data/roman-translation-lighting.json').read_text())
PROFILE_ID=PROFILE['profileId']


def padding(em):
    g=PROFILE['outerGlow'];r=PROFILE['rendering']
    return .5+em/500*g['size']*(g['spread']+r['sizeToGaussianSigma']*r['blurTruncate'])


def tile(path,area,em,scale,component):
    from .paint import mask,rgb,vector_distance
    p=PROFILE;unit=em*scale/500;alpha=mask(path,area,scale)
    result=np.zeros((*alpha.shape,4),dtype=np.float32)
    def blur(value,size):
        return gaussian_filter(value,max(.01,size*unit*p['rendering']['sizeToGaussianSigma']),truncate=3,mode='constant')
    def over(color,coverage):
        coverage=np.clip(coverage,0,1)
        result[:,:,:3]=result[:,:,:3]*(1-coverage[:,:,None])+color*coverage[:,:,None]
        result[:,:,3]=result[:,:,3]*(1-coverage)+coverage
    def gradient(colors,amount):
        # Both archived glow gradients fade to transparent at the far stop.
        near,far=map(rgb,colors)
        return far+(near-far)*amount[:,:,None]
    if component!='surface':
        g=p['outerGlow'];distance=distance_transform_edt(alpha<.5)
        spread=np.maximum(alpha,np.clip(g['size']*g['spread']*unit+.5-distance,0,1))
        amount=np.clip(blur(spread,g['size'])/g['range'],0,1)
        curve=np.asarray(g['contour']);amount=np.interp(amount,curve[:,0],curve[:,1])
        over(gradient(g['colors'],amount),amount*g['opacity']*(1-alpha))
    if component!='glow':
        # Satin shades the solid blue face; edge glow is screened above it.
        s=p['satin'];angle=math.radians(s['angle']);offset=(math.sin(angle)*s['distance']*unit,math.cos(angle)*s['distance']*unit)
        field=blur(alpha,s['size'])
        difference=np.abs(shift(field,offset,order=1,mode='constant',prefilter=False)-shift(field,tuple(-v for v in offset),order=1,mode='constant',prefilter=False))
        curve=np.asarray(s['contour']);satin=np.interp(np.clip(difference,0,1),curve[:,0],curve[:,1])
        if s['invert']:satin=1-satin
        color=rgb(p['fill'])*(1-satin[:,:,None]*s['opacity'])
        g=p['innerGlow'];amount=np.clip((1-blur(alpha,g['size']))/g['range'],0,1)
        color=1-(1-color)*(1-gradient(g['colors'],amount)*amount[:,:,None]*g['opacity'])
        b=p['bevel'];distance=vector_distance(path,alpha,area,scale)
        size=max(.1,b['size']*unit)
        # Smooth inner-bevel cross section, unlike the script's chiseled rim.
        height=np.sin(np.clip(distance/size,0,1)*math.pi/2)*size
        height=gaussian_filter(height,.7,truncate=3)
        dy,dx=np.gradient(height);nx=-dx*b['depth'];ny=-dy*b['depth']
        norm=np.sqrt(nx*nx+ny*ny+1);az=math.radians(b['azimuth']);el=math.radians(b['elevation'])
        light=(nx*math.cos(az)*math.cos(el)-ny*math.sin(az)*math.cos(el)+math.sin(el))/norm
        intensity=np.clip((light-math.sin(el))*2,-1,1)
        color*=1+np.minimum(intensity,0)[:,:,None]*b['shadowOpacity']
        color=1-(1-color)*(1-rgb(b['highlight'])*np.maximum(intensity,0)[:,:,None]*b['highlightOpacity'])
        over(color,alpha)
    a=result[:,:,3:4];color=np.divide(result[:,:,:3],a,out=np.zeros_like(result[:,:,:3]),where=a>0)
    rgba=np.clip(np.concatenate((color,a),axis=2)*255+.5,0,255).astype(np.uint8)
    h,w=alpha.shape
    return QImage(rgba.data,w,h,w*4,QImage.Format.Format_RGBA8888).copy()
