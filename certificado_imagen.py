# -*- coding: utf-8 -*-
"""Generación del certificado usando siempre la plantilla oficial del hospital."""
from __future__ import annotations
import io, os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

ROOT=os.path.dirname(os.path.abspath(__file__))
PLANTILLAS=[os.path.join(ROOT,"assets",x) for x in ("certificado_base.png","certificado_base.jpg","certificado_base.jpeg")]
W,H=1536,1024
TINTA=(28,42,68); ORO=(176,141,68)

def _font(size,bold=False):
    paths=["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf","/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf","C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"]
    for p in paths:
        if os.path.isfile(p):
            try:return ImageFont.truetype(p,size)
            except Exception:pass
    return ImageFont.load_default()

def _tw(draw,text,font):
    b=draw.textbbox((0,0),text,font=font); return b[2]-b[0]

def _center(draw,text,y,font,max_w=None):
    max_w=max_w or int(W*.72); lines=[]; cur=""
    for word in (text or "").split():
        test=(cur+" "+word).strip()
        if _tw(draw,test,font)<=max_w:cur=test
        else:
            if cur:lines.append(cur)
            cur=word
    if cur or not lines:lines.append(cur)
    lh=getattr(font,"size",18)+8
    for i,line in enumerate(lines):draw.text(((W-_tw(draw,line,font))//2,y+i*lh),line,font=font,fill=TINTA)
    return len(lines)*lh

def _signature(img,path,box):
    if not path or not os.path.isfile(path):return
    try:
        sign=Image.open(path).convert("RGBA"); sign.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS)
        img.paste(sign,(box[0]+(box[2]-sign.width)//2,box[1]+(box[3]-sign.height)//2),sign)
    except Exception as exc:print("[certificado] firma:",exc)

def generar_certificado(*,nombre_receptor,titulo,hospital="Hospital General",emisor="Encargado",fecha="",numero="",descripcion="",departamento="",capacitacion="",cedula="",firma_encargado_path=None,firma_director_path=None,firma_director_zona_path=None,label_encargado="Otorgado por / Encargado",label_director="Director de Investigación y Docencia",label_director_zona="Director del Ala / Departamento"):
    base=None
    for path in PLANTILLAS:
        if os.path.isfile(path):
            try:base=Image.open(path).convert("RGBA");break
            except Exception:pass
    img=base or Image.new("RGBA",(W,H),(248,243,232,255))
    if img.size!=(W,H):img=img.resize((W,H),Image.Resampling.LANCZOS)
    draw=ImageDraw.Draw(img); f1=_font(22); fn=_font(45,True); ft=_font(30,True); fb=_font(18); fl=_font(14)
    y=int(H*.34); y+=_center(draw,"Se certifica que",y,f1)+10; y+=_center(draw,nombre_receptor or "—",y,fn)+8
    draw.line(((W-500)//2,y,(W+500)//2,y),fill=ORO,width=1); y+=18
    y+=_center(draw,"ha completado satisfactoriamente la certificación:",y,f1)+10; y+=_center(draw,'"'+(capacitacion or titulo or "Certificación")+'"',y,ft)
    if cedula:y+=10; y+=_center(draw,"Identificación: "+cedula,y,fb)
    if descripcion:y+=8; y+=_center(draw,descripcion,y,fb,int(W*.65))
    if departamento:y+=8; y+=_center(draw,"Área / departamento: "+departamento,y,fb)
    fecha=fecha or datetime.utcnow().strftime("%d/%m/%Y"); numero=numero or "CERT-00000"
    _center(draw,f"Fecha: {fecha}   ·   N.º {numero}",max(y+20,int(H*.67)),fb)
    boxes=[(int(W*.04),int(H*.75),int(W*.27),int(H*.10)),(int(W*.365),int(H*.75),int(W*.27),int(H*.10)),(int(W*.695),int(H*.75),int(W*.27),int(H*.10))]
    for box,path,label in zip(boxes,(firma_encargado_path,firma_director_path,firma_director_zona_path),(label_encargado,label_director,label_director_zona)):
        _signature(img,path,box); ly=int(H*.87); draw.line((box[0],ly,box[0]+box[2],ly),fill=ORO,width=1)
        tw=_tw(draw,label,fl); draw.text((box[0]+(box[2]-tw)//2,ly+6),label,font=fl,fill=TINTA)
    out=io.BytesIO(); img.convert("RGB").save(out,"PNG",optimize=True); out.seek(0); return out
