// Exercise the production hooks against the verified 4.1 prelude sequence.
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>
using P=void*;using M=const void*;
#define LOG(...) ((void)0)
struct Object {std::string name;P clip=nullptr;};
static Object mainSource{"main"},drumSource{"drum"},introSource{"intro"},prelude{"prelude"},manager{"manager"},musics{"musics"};
static std::map<int,Object> originals;
static std::map<std::string,Object> bank;
static std::map<uint32_t,P> handles;
static uint32_t nextHandle=0;
static bool blooms=true;
static unsigned resourceLoads=0,audioLoads=0,reflections=0,cleanups=0;
static std::vector<P> decoded;
static P stat(const char*,const char* f){++reflections;std::string n=f;return n=="music"?&mainSource:n=="musicDrum"?&drumSource:n=="prelude"?&prelude:&manager;}
template<class T>static T field(P,const char* f){++reflections;return reinterpret_cast<T>(std::string(f)=="audioSource"?&introSource:&musics);}
static uint32_t il2cpp_gchandle_new(P o,bool){handles[++nextHandle]=o;return nextHandle;}
static void il2cpp_gchandle_free(uint32_t h){assert(handles.erase(h)==1);}
static P target(uint32_t h){return h?handles.at(h):nullptr;}
static void release(uint32_t& h){if(h)il2cpp_gchandle_free(h);h=0;}
static P cls(const char*,const char*){return &manager;}
static P il2cpp_class_get_type(P p){return p;}
static P il2cpp_type_get_object(P p){return p;}
static M method(P,const char* n,int){return n;}
static M overload(P,const char* n,std::initializer_list<const char*>){return n;}
static P str(const char* n){static std::string text;text=n;return &text;}
static bool alive(P p){return p!=nullptr;}
static std::string name(P p){return static_cast<Object*>(p)->name;}
template<class T>static T value(P p){return p?*static_cast<T*>(p):T{};}
static P call(M m,P=nullptr,P* args=nullptr){
    ++reflections;std::string n=static_cast<const char*>(m);
    if(n=="UnloadUnusedAssets"){++cleanups;return nullptr;}
    assert(n=="Load");++resourceLoads;
    auto it=bank.find(*static_cast<std::string*>(args[0]));return it==bank.end()?nullptr:&it->second;
}
static P call(P o,const char* n,int=0,P* args=nullptr){
    ++reflections;if(!o)return nullptr;
    if(std::string(n)=="get_clip")return static_cast<Object*>(o)->clip;
    assert(std::string(n)=="get_Item");return &originals.at(*static_cast<int*>(args[0]));
}
#include "../music_profiles.inc"
static bool nativeLoad(P p,M){++audioLoads;decoded.push_back(p);return true;}
static void nativeSet(P o,P p,M){static_cast<Object*>(o)->clip=p;}
static void nativePlay(P,int id,M){
    if(id==12){
        setMusicClip(&introSource,&originals.at(12),nullptr);
        loadMusicData(&originals.at(10),nullptr);loadMusicData(&originals.at(11),nullptr);
    }else{
        setMusicClip(&mainSource,&originals.at(id),nullptr);
        if(id==10)setMusicClip(&drumSource,&originals.at(11),nullptr);
    }
}
int main(){
    for(auto row:std::map<int,std::string>{{0,"MainMenu"},{10,"Roof"},{11,"Roof_drum"},{12,"Roof_pre"},{26,"HorseBoss"},{27,"Unreviewed_New_Track"}}){
        originals.emplace(row.first,Object{row.second});
        auto lower=row.second;std::transform(lower.begin(),lower.end(),lower.begin(),::tolower);
        if(row.first!=27)bank.emplace("englishmusic/original/"+lower,Object{"Original "+row.second});
        if(row.first!=26&&row.first!=27)bank.emplace("englishmusic/blooms/"+lower,Object{"Blooms "+row.second});
    }
    oldSetMusicClip=nativeSet;oldProfilePlayMusic=nativePlay;oldLoadMusicData=nativeLoad;
    Object sfx{"SFX"};unsigned before=reflections;
    setMusicClip(&sfx,&originals.at(0),nullptr);
    assert(sfx.clip==&originals.at(0)&&reflections==before&&audioLoads==0);
    profilePlayMusic(nullptr,12,nullptr);
    assert(name(introSource.clip)=="Blooms Roof_pre");
    assert(decoded.size()==3);for(P p:decoded)assert(name(p).find("Blooms ")==0);
    assert(musicClipCache.size()==3); // Intro plus the two native preloads.
    auto loads=resourceLoads;auto decodes=audioLoads;
    profilePlayMusic(nullptr,10,nullptr);
    assert(name(mainSource.clip)=="Blooms Roof"&&name(drumSource.clip)=="Blooms Roof_drum");
    assert(resourceLoads==loads&&audioLoads==decodes); // Reuse warmed stems.
    assert(!preludeWarmOriginal[0]&&!preludeWarmOriginal[1]);
    loadMusicData(&originals.at(10),nullptr);assert(decoded.back()==&originals.at(10));
    profilePlayMusic(nullptr,26,nullptr);assert(name(mainSource.clip)=="Original HorseBoss");
    profilePlayMusic(nullptr,27,nullptr);assert(mainSource.clip==&originals.at(27));
    blooms=false;profilePlayMusic(nullptr,12,nullptr);
    assert(name(introSource.clip)=="Original Roof_pre");
    profilePlayMusic(nullptr,10,nullptr);assert(name(mainSource.clip)=="Original Roof");
    // Many transitions retire inactive clips; references remain bounded.
    for(int i=0;i<100;++i){profilePlayMusic(nullptr,i%2?0:10,nullptr);assert(musicClipCache.size()<=3);}
    assert(cleanups>0&&handles.size()<=6);
    before=reflections;setMusicClip(&sfx,&originals.at(10),nullptr);
    assert(sfx.clip==&originals.at(10)&&reflections==before);
    std::cout<<"Music profiles: prelude, native preloads, reuse, fallback, SFX isolation and 100 transitions passed\n";
}
