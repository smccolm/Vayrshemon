// M14: native, bounded, read-only COM icon and isolated thumbnail provider.
// No Python, Qt, fonts, registry writes, network services or document execution.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <thumbcache.h>
#include <wincodec.h>
#include <wincrypt.h>
#include <wrl/client.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
using Microsoft::WRL::ComPtr;
// Keep in sync with tools/windows_shell.py.
const CLSID CLSID_VayShell={0x7b6ea804,0x42e7,0x4bfc,{0xa5,0x62,0x42,0x95,0xcc,0xd2,0x7b,0x61}};
static HMODULE module;
static std::atomic<long> objects{0};
static constexpr size_t MAX_FILE=16*1024*1024,MAX_PNG=3*1024*1024;

// Strict JSON token walker. Only root preview fields are retained. Bound every
// input/allocation, recursion depth and token count before invoking WIC.
class Json {
    std::string_view s;size_t p=0,tokens=0;
    void ws(){while(p<s.size()&&(s[p]==' '||s[p]=='\t'||s[p]=='\r'||s[p]=='\n'))++p;}
    void expect(char c){ws();if(p>=s.size()||s[p++]!=c)throw std::runtime_error("json");}
    std::string string(){
        expect('"');std::string out;
        while(p<s.size()){
            unsigned char c=s[p++];if(c=='"')return out;
            if(c<32)throw std::runtime_error("control");
            if(c=='\\'){
                if(p==s.size())throw std::runtime_error("escape");c=s[p++];
                if(c=='u'){
                    unsigned u=0;for(int i=0;i<4;++i){if(p==s.size())throw std::runtime_error("unicode");char h=s[p++];u*=16;if(h>='0'&&h<='9')u+=h-'0';else if(h>='a'&&h<='f')u+=h-'a'+10;else if(h>='A'&&h<='F')u+=h-'A'+10;else throw std::runtime_error("hex");}
                    if(u<128)out+=char(u);else {out+='\\';out+='u';out+=std::to_string(u);out+=';';}
                    continue;
                }
                switch(c){case '"':case '\\':case '/':break;case 'b':c='\b';break;case 'f':c='\f';break;case 'n':c='\n';break;case 'r':c='\r';break;case 't':c='\t';break;default:throw std::runtime_error("escape");}
            }
            out+=char(c);if(out.size()>4*1024*1024)throw std::runtime_error("string limit");
        }throw std::runtime_error("string end");
    }
    void value(unsigned depth){
        ws();if(depth>64||++tokens>400000||p>=s.size())throw std::runtime_error("limit");char c=s[p];
        if(c=='{'){object(depth+1);return;}
        if(c=='['){++p;ws();if(p<s.size()&&s[p]==']'){++p;return;}do{value(depth+1);ws();if(p<s.size()&&s[p]==']'){++p;return;}expect(',');}while(true);}
        if(c=='"'){string();return;}
        for(auto word:{"true","false","null"}){size_t n=strlen(word);if(s.substr(p,n)==word){p+=n;return;}}
        if(c=='-')++p;
        if(p>=s.size())throw std::runtime_error("number");
        if(s[p]=='0')++p;else {size_t start=p;while(p<s.size()&&s[p]>='0'&&s[p]<='9')++p;if(p==start)throw std::runtime_error("number");}
        auto digits=[&](){size_t start=p;while(p<s.size()&&s[p]>='0'&&s[p]<='9')++p;if(p==start)throw std::runtime_error("digits");};
        if(p<s.size()&&s[p]=='.'){++p;digits();}
        if(p<s.size()&&(s[p]=='e'||s[p]=='E')){++p;if(p<s.size()&&(s[p]=='+'||s[p]=='-'))++p;digits();}
    }
    std::map<std::string,std::string_view> object(unsigned depth){
        expect('{');std::map<std::string,std::string_view> fields;ws();if(p<s.size()&&s[p]=='}'){++p;return fields;}
        do{
            auto key=string();expect(':');ws();size_t start=p;value(depth);
            if(!fields.emplace(key,s.substr(start,p-start)).second||fields.size()>20000)throw std::runtime_error("duplicate or limit");
            ws();if(p<s.size()&&s[p]=='}'){++p;return fields;}expect(',');
        }while(true);
    }
public:
    explicit Json(std::string_view text):s(text){}
    std::map<std::string,std::string_view> fields(){auto f=object(0);ws();if(p!=s.size())throw std::runtime_error("trailing");return f;}
    std::string text(){auto t=string();ws();if(p!=s.size())throw std::runtime_error("trailing");return t;}
};

struct Preview {std::string mode="color";std::vector<BYTE> png;};
static Preview parse(const std::string& raw){
    auto root=Json(raw).fields();
    if(Json(root.at("format")).text()!="vayrshemon.document")throw std::runtime_error("format");
    auto found=root.find("shellPreview");if(found==root.end())return {};
    auto fields=Json(found->second).fields();
    if(fields.at("version")!="1")throw std::runtime_error("version");
    Preview preview;preview.mode=Json(fields.at("colorMode")).text();
    if(preview.mode!="color"&&preview.mode!="mono-black"&&preview.mode!="mono-white")throw std::runtime_error("mode");
    auto encoded=Json(fields.at("pngBase64")).text();
    if(encoded.empty()||encoded.size()>MAX_PNG*4/3)throw std::runtime_error("png limit");
    DWORD length=0;
    if(!CryptStringToBinaryA(encoded.data(),DWORD(encoded.size()),CRYPT_STRING_BASE64|CRYPT_STRING_STRICT,nullptr,&length,nullptr,nullptr)||length>MAX_PNG)throw std::runtime_error("base64");
    preview.png.resize(length);
    if(!CryptStringToBinaryA(encoded.data(),DWORD(encoded.size()),CRYPT_STRING_BASE64|CRYPT_STRING_STRICT,preview.png.data(),&length,nullptr,nullptr))throw std::runtime_error("base64");
    const BYTE sig[]={137,80,78,71,13,10,26,10};
    if(length<33||memcmp(preview.png.data(),sig,8))throw std::runtime_error("png header");
    return preview;
}

static HRESULT read_stream(IStream* stream,Preview& preview){
    if(!stream)return E_INVALIDARG;
    try {
        STATSTG st={};HRESULT hr=stream->Stat(&st,STATFLAG_NONAME);if(FAILED(hr))return hr;
        if(st.cbSize.QuadPart==0||st.cbSize.QuadPart>MAX_FILE)return HRESULT_FROM_WIN32(ERROR_FILE_TOO_LARGE);
        LARGE_INTEGER zero={};hr=stream->Seek(zero,STREAM_SEEK_SET,nullptr);if(FAILED(hr))return hr;
        std::string data(size_t(st.cbSize.QuadPart),'\0');ULONG received=0;
        hr=stream->Read(data.data(),ULONG(data.size()),&received);if(FAILED(hr))return hr;
        if(received!=data.size())return STG_E_READFAULT;
        preview=parse(data);return S_OK;
    }catch(const std::bad_alloc&){return E_OUTOFMEMORY;}catch(...){return HRESULT_FROM_WIN32(ERROR_INVALID_DATA);}
}

static HRESULT thumbnail(const Preview& preview,UINT edge,HBITMAP* bitmap,WTS_ALPHATYPE* alpha){
    if(!bitmap||!alpha)return E_POINTER;*bitmap=nullptr;*alpha=WTSAT_UNKNOWN;
    if(preview.png.empty()||!edge||edge>4096)return E_INVALIDARG;
    ComPtr<IWICImagingFactory> factory;HRESULT hr=CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&factory));if(FAILED(hr))return hr;
    ComPtr<IWICStream> stream;hr=factory->CreateStream(&stream);if(FAILED(hr))return hr;
    hr=stream->InitializeFromMemory(const_cast<BYTE*>(preview.png.data()),DWORD(preview.png.size()));if(FAILED(hr))return hr;
    ComPtr<IWICBitmapDecoder> decoder;hr=factory->CreateDecoderFromStream(stream.Get(),nullptr,WICDecodeMetadataCacheOnLoad,&decoder);if(FAILED(hr))return hr;
    GUID format;hr=decoder->GetContainerFormat(&format);if(FAILED(hr)||format!=GUID_ContainerFormatPng)return E_INVALIDARG;
    ComPtr<IWICBitmapFrameDecode> frame;hr=decoder->GetFrame(0,&frame);if(FAILED(hr))return hr;
    UINT w=0,h=0;hr=frame->GetSize(&w,&h);if(FAILED(hr)||!w||!h||w>1024||h>1024)return E_INVALIDARG;
    double factor=std::min(1.0,double(edge)/std::max(w,h));w=std::max(1u,UINT(std::round(w*factor)));h=std::max(1u,UINT(std::round(h*factor)));
    ComPtr<IWICBitmapScaler> scaler;hr=factory->CreateBitmapScaler(&scaler);if(FAILED(hr))return hr;
    hr=scaler->Initialize(frame.Get(),w,h,WICBitmapInterpolationModeFant);if(FAILED(hr))return hr;
    ComPtr<IWICFormatConverter> convert;hr=factory->CreateFormatConverter(&convert);if(FAILED(hr))return hr;
    hr=convert->Initialize(scaler.Get(),GUID_WICPixelFormat32bppPBGRA,WICBitmapDitherTypeNone,nullptr,0,WICBitmapPaletteTypeCustom);if(FAILED(hr))return hr;
    BITMAPINFO info={};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);info.bmiHeader.biWidth=w;info.bmiHeader.biHeight=-LONG(h);info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;info.bmiHeader.biCompression=BI_RGB;
    void* bits=nullptr;HBITMAP result=CreateDIBSection(nullptr,&info,DIB_RGB_COLORS,&bits,nullptr,0);if(!result)return E_OUTOFMEMORY;
    hr=convert->CopyPixels(nullptr,w*4,w*h*4,static_cast<BYTE*>(bits));if(FAILED(hr)){DeleteObject(result);return hr;}
    *bitmap=result;*alpha=WTSAT_ARGB;return S_OK;
}

class Handler final:public IThumbnailProvider,public IInitializeWithStream,public IPersistFile,public IExtractIconW {
    std::atomic<ULONG> refs{1};bool initialized=false;Preview preview;
public:
    Handler(){++objects;}~Handler(){--objects;}
    IFACEMETHODIMP QueryInterface(REFIID iid,void** out)override{
        if(!out)return E_POINTER;*out=nullptr;
        if(iid==IID_IUnknown||iid==IID_IThumbnailProvider)*out=static_cast<IThumbnailProvider*>(this);
        else if(iid==IID_IInitializeWithStream)*out=static_cast<IInitializeWithStream*>(this);
        else if(iid==IID_IPersist||iid==IID_IPersistFile)*out=static_cast<IPersistFile*>(this);
        else if(iid==IID_IExtractIconW)*out=static_cast<IExtractIconW*>(this);
        else return E_NOINTERFACE;AddRef();return S_OK;
    }
    IFACEMETHODIMP_(ULONG) AddRef()override{return ++refs;}
    IFACEMETHODIMP_(ULONG) Release()override{ULONG n=--refs;if(!n)delete this;return n;}
    IFACEMETHODIMP Initialize(IStream* stream,DWORD)override{if(initialized)return HRESULT_FROM_WIN32(ERROR_ALREADY_INITIALIZED);HRESULT hr=read_stream(stream,preview);if(SUCCEEDED(hr))initialized=true;return hr;}
    IFACEMETHODIMP GetThumbnail(UINT edge,HBITMAP* bitmap,WTS_ALPHATYPE* alpha)override{
        if(!initialized)return E_UNEXPECTED;return thumbnail(preview,edge,bitmap,alpha);
    }
    IFACEMETHODIMP GetClassID(CLSID* clsid)override{if(!clsid)return E_POINTER;*clsid=CLSID_VayShell;return S_OK;}
    IFACEMETHODIMP IsDirty()override{return S_FALSE;}
    IFACEMETHODIMP Load(LPCOLESTR path,DWORD)override{
        if(!path)return E_INVALIDARG;ComPtr<IStream> stream;
        HRESULT hr=SHCreateStreamOnFileEx(path,STGM_READ|STGM_SHARE_DENY_NONE,FILE_ATTRIBUTE_NORMAL,FALSE,nullptr,&stream);if(FAILED(hr))return hr;return Initialize(stream.Get(),STGM_READ);
    }
    IFACEMETHODIMP Save(LPCOLESTR,BOOL)override{return E_NOTIMPL;}
    IFACEMETHODIMP SaveCompleted(LPCOLESTR)override{return E_NOTIMPL;}
    IFACEMETHODIMP GetCurFile(LPOLESTR* file)override{if(file)*file=nullptr;return E_NOTIMPL;}
    IFACEMETHODIMP GetIconLocation(UINT,LPWSTR file,UINT count,int* index,UINT* flags)override{
        if(!initialized)return E_UNEXPECTED;if(!file||!index||!flags)return E_POINTER;
        wchar_t path[32768];DWORD n=GetModuleFileNameW(module,path,32768);if(!n||n>=32768)return E_FAIL;
        wchar_t* slash=wcsrchr(path,L'\\');if(!slash)return E_FAIL;*(slash+1)=0;
        const wchar_t* icon=preview.mode=="mono-white"?L"memon-mono-white.ico":preview.mode=="mono-black"?L"memon-mono-black.ico":L"memon-color.ico";
        if(wcslen(path)+wcslen(icon)+1>count)return HRESULT_FROM_WIN32(ERROR_INSUFFICIENT_BUFFER);
        wcscpy_s(file,count,path);wcscat_s(file,count,icon);*index=0;*flags=GIL_PERINSTANCE;return S_OK;
    }
    IFACEMETHODIMP Extract(LPCWSTR,UINT,HICON* largeIcon,HICON* smallIcon,UINT)override{if(largeIcon)*largeIcon=nullptr;if(smallIcon)*smallIcon=nullptr;return S_FALSE;}
};

class Factory final:public IClassFactory {
    std::atomic<ULONG> refs{1};
public:
    Factory(){++objects;}~Factory(){--objects;}
    IFACEMETHODIMP QueryInterface(REFIID iid,void** out)override{if(!out)return E_POINTER;*out=nullptr;if(iid!=IID_IUnknown&&iid!=IID_IClassFactory)return E_NOINTERFACE;*out=this;AddRef();return S_OK;}
    IFACEMETHODIMP_(ULONG) AddRef()override{return ++refs;}
    IFACEMETHODIMP_(ULONG) Release()override{ULONG n=--refs;if(!n)delete this;return n;}
    IFACEMETHODIMP CreateInstance(IUnknown* outer,REFIID iid,void** out)override{
        if(!out)return E_POINTER;*out=nullptr;if(outer)return CLASS_E_NOAGGREGATION;
        auto handler=new(std::nothrow) Handler();if(!handler)return E_OUTOFMEMORY;HRESULT hr=handler->QueryInterface(iid,out);handler->Release();return hr;
    }
    IFACEMETHODIMP LockServer(BOOL lock)override{if(lock)++objects;else --objects;return S_OK;}
};
extern "C" HRESULT __stdcall DllGetClassObject(REFCLSID clsid,REFIID iid,void** out){
    if(!out)return E_POINTER;*out=nullptr;if(clsid!=CLSID_VayShell)return CLASS_E_CLASSNOTAVAILABLE;
    auto factory=new(std::nothrow) Factory();if(!factory)return E_OUTOFMEMORY;HRESULT hr=factory->QueryInterface(iid,out);factory->Release();return hr;
}
extern "C" HRESULT __stdcall DllCanUnloadNow(){return objects==0?S_OK:S_FALSE;}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,void*){if(reason==DLL_PROCESS_ATTACH){module=instance;DisableThreadLibraryCalls(instance);}return TRUE;}
