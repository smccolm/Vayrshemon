"""Exercise the real native COM provider and Windows Shell image factory.

Direct mode needs no registry changes. Shell mode verifies installed Explorer
integration, including the OS thumbnail surrogate, rather than a Python mock.
"""
import ctypes as C
from ctypes import wintypes as W
from pathlib import Path
import uuid
from PySide6.QtGui import QImage
from .windows_shell import CLSID

HRESULT=C.c_long


class GUID(C.Structure):
    _fields_=[('bytes',C.c_ubyte*16)]
    def __init__(self,text):super().__init__((C.c_ubyte*16).from_buffer_copy(uuid.UUID(text.strip('{}')).bytes_le))


def checked(hr):
    if hr<0:raise OSError(f'COM HRESULT 0x{hr & 0xffffffff:08X}')


def call(pointer,index,result,*types):
    table=C.cast(pointer,C.POINTER(C.POINTER(C.c_void_p))).contents
    return C.WINFUNCTYPE(result,C.c_void_p,*types)(table[index])


def release(pointer):
    if pointer:call(pointer,2,W.ULONG)(pointer)


def query(pointer,iid):
    result=C.c_void_p();checked(call(pointer,0,HRESULT,C.POINTER(GUID),C.POINTER(C.c_void_p))(pointer,C.byref(GUID(iid)),C.byref(result)));return result


def bitmap_image(bitmap):
    class Bitmap(C.Structure):
        _fields_=[('type',W.LONG),('width',W.LONG),('height',W.LONG),('stride',W.LONG),('planes',W.WORD),('bitsPixel',W.WORD),('bits',C.c_void_p)]
    class Header(C.Structure):
        _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),('compression',W.DWORD),('sizeImage',W.DWORD),('x',W.LONG),('y',W.LONG),('used',W.DWORD),('important',W.DWORD)]
    gdi=C.windll.gdi32;gdi.GetObjectW.argtypes=[C.c_void_p,C.c_int,C.c_void_p];gdi.DeleteObject.argtypes=[C.c_void_p]
    data=Bitmap()
    try:
        if not gdi.GetObjectW(bitmap,C.sizeof(data),C.byref(data)):raise C.WinError()
        w,h=data.width,abs(data.height);header=Header(C.sizeof(Header),w,-h,1,32,0,w*h*4,0,0,0,0);bits=C.create_string_buffer(w*h*4)
        user=C.windll.user32;user.GetDC.argtypes=[C.c_void_p];user.GetDC.restype=C.c_void_p;user.ReleaseDC.argtypes=[C.c_void_p,C.c_void_p]
        dc=user.GetDC(None);gdi.GetDIBits.argtypes=[C.c_void_p,C.c_void_p,W.UINT,W.UINT,C.c_void_p,C.c_void_p,W.UINT]
        try:
            if not gdi.GetDIBits(dc,bitmap,0,h,bits,C.byref(header),0):raise C.WinError()
        finally:user.ReleaseDC(None,dc)
        return QImage(bits.raw,w,h,w*4,QImage.Format.Format_ARGB32_Premultiplied).copy()
    finally:gdi.DeleteObject(bitmap)


def direct(dll,path,edge=256):
    ole=C.OleDLL('ole32');ole.CoInitializeEx(None,2)
    library=C.WinDLL(str(dll));factory=C.c_void_p();obj=C.c_void_p();stream=C.c_void_p();thumb=C.c_void_p();icon=C.c_void_p();initialize=C.c_void_p()
    library.DllGetClassObject.argtypes=[C.POINTER(GUID),C.POINTER(GUID),C.POINTER(C.c_void_p)];library.DllGetClassObject.restype=HRESULT
    try:
        checked(library.DllGetClassObject(C.byref(GUID(CLSID)),C.byref(GUID('00000001-0000-0000-C000-000000000046')),C.byref(factory)))
        checked(call(factory,3,HRESULT,C.c_void_p,C.POINTER(GUID),C.POINTER(C.c_void_p))(factory,None,C.byref(GUID('00000000-0000-0000-C000-000000000046')),C.byref(obj)))
        initialize=query(obj,'B824B49D-22AC-4161-AC8A-9916E8FA3F7F')
        sh=C.WinDLL('shlwapi');sh.SHCreateStreamOnFileEx.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,W.BOOL,C.c_void_p,C.POINTER(C.c_void_p)];sh.SHCreateStreamOnFileEx.restype=HRESULT
        checked(sh.SHCreateStreamOnFileEx(str(Path(path).resolve()),0x40,0,False,None,C.byref(stream)))
        checked(call(initialize,3,HRESULT,C.c_void_p,W.DWORD)(initialize,stream,0))
        icon=query(obj,'000214FA-0000-0000-C000-000000000046');location=C.create_unicode_buffer(32768);index=C.c_int();flags=W.UINT()
        checked(call(icon,3,HRESULT,W.UINT,W.LPWSTR,W.UINT,C.POINTER(C.c_int),C.POINTER(W.UINT))(icon,0,location,32768,C.byref(index),C.byref(flags)))
        thumb=query(obj,'E357FCCD-A995-4576-B01F-234630154E96');bitmap=C.c_void_p();alpha=C.c_int()
        checked(call(thumb,3,HRESULT,W.UINT,C.POINTER(C.c_void_p),C.POINTER(C.c_int))(thumb,edge,C.byref(bitmap),C.byref(alpha)))
        return dict(icon=location.value,alpha=alpha.value),bitmap_image(bitmap)
    finally:
        for pointer in (thumb,icon,initialize,stream,obj,factory):release(pointer)


def shell(path,edge=256,icon=False):
    C.OleDLL('ole32').CoInitializeEx(None,2);api=C.WinDLL('shell32');factory=C.c_void_p()
    api.SHCreateItemFromParsingName.argtypes=[W.LPCWSTR,C.c_void_p,C.POINTER(GUID),C.POINTER(C.c_void_p)];api.SHCreateItemFromParsingName.restype=HRESULT
    class Size(C.Structure):_fields_=[('cx',C.c_long),('cy',C.c_long)]
    try:
        checked(api.SHCreateItemFromParsingName(str(Path(path).resolve()),None,C.byref(GUID('BCC18B79-BA16-442F-80C4-8A59C30C463B')),C.byref(factory)))
        bitmap=C.c_void_p()
        checked(call(factory,3,HRESULT,Size,C.c_int,C.POINTER(C.c_void_p))(factory,Size(edge,edge),0x04 if icon else 0x08,C.byref(bitmap)))
        return bitmap_image(bitmap)
    finally:release(factory)
