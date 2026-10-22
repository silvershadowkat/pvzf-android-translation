// Display-only IL2CPP integration. All Unity operations run on Unity's main thread.
// No game offsets, gameplay string keys, or save structures are rewritten here.
#include <jni.h>
#include <dlfcn.h>
#include <unistd.h>
#include <android/log.h>
#include <dobby.h>
#include <string>
#include <vector>
#include <unordered_map>
#include <thread>
#include <cstring>
#include <chrono>
#include <algorithm>
#include <mutex>
#include <cmath>
#include "field_access.h"

using P=void*;
using M=const void*;
#define LOG(...) __android_log_print(ANDROID_LOG_INFO,"PvZFEnglish",__VA_ARGS__)
#define API(ret,name,args) static ret (*name) args
API(P,il2cpp_domain_get,());
API(P*,il2cpp_domain_get_assemblies,(P,size_t*));
API(P,il2cpp_assembly_get_image,(P));
API(P,il2cpp_class_from_name,(P,const char*,const char*));
API(M,il2cpp_class_get_method_from_name,(P,const char*,int));
API(M,il2cpp_class_get_methods,(P,P*));
API(const char*,il2cpp_method_get_name,(M));
API(uint32_t,il2cpp_method_get_param_count,(M));
API(P,il2cpp_method_get_param,(M,uint32_t));
API(char*,il2cpp_type_get_name,(P));
API(void,il2cpp_free,(P));
API(P,il2cpp_class_get_type,(P));
API(P,il2cpp_type_get_object,(P));
API(P,il2cpp_object_get_class,(P));
API(P,il2cpp_class_get_field_from_name,(P,const char*));
API(void,il2cpp_field_get_value,(P,P,P));
API(void,il2cpp_field_set_value,(P,P,P));
API(void,il2cpp_field_set_value_object,(P,P,P));
API(void,il2cpp_field_static_get_value,(P,P));
API(P,il2cpp_runtime_invoke,(M,P,P*,P*));
API(P,il2cpp_object_unbox,(P));
API(P,il2cpp_object_new,(P));
API(P,il2cpp_string_new,(const char*));
API(P,il2cpp_string_new_utf16,(const char16_t*,int32_t));
API(const char16_t*,il2cpp_string_chars,(P));
API(int32_t,il2cpp_string_length,(P));
API(uint32_t,il2cpp_gchandle_new,(P,bool));
API(P,il2cpp_gchandle_get_target,(uint32_t));
API(void,il2cpp_gchandle_free,(uint32_t));
API(uintptr_t,il2cpp_array_length,(P));
API(P,il2cpp_thread_attach,(P));
API(void,il2cpp_thread_detach,(P));

static JavaVM* vm;
static jclass bridge;
static jmethodID translateJava,saveMusicJava,onlineTitleJava,registerOnlineJava;
static std::string runtimeRoot;
static bool blooms=true;
static std::unordered_map<std::string,P> classes;
static std::mutex classMutex;
static JNIEnv* env(){JNIEnv* e=nullptr;if(vm->GetEnv((P*)&e,JNI_VERSION_1_6)!=JNI_OK)return nullptr;return e;}
static P cls(const char* ns,const char* name){
    std::lock_guard<std::mutex> lock(classMutex);
    std::string key=std::string(ns)+"."+name;auto found=classes.find(key);if(found!=classes.end())return found->second;
    size_t n=0;P* as=il2cpp_domain_get_assemblies(il2cpp_domain_get(),&n);
    for(size_t i=0;i<n;i++)if(P c=il2cpp_class_from_name(il2cpp_assembly_get_image(as[i]),ns,name)){classes[key]=c;return c;}
    return nullptr;
}
static M method(P c,const char* name,int n){return c?il2cpp_class_get_method_from_name(c,name,n):nullptr;}
static M overload(P c,const char* name,std::initializer_list<const char*> types){
    if(!c)return nullptr;P it=nullptr;
    while(M m=il2cpp_class_get_methods(c,&it)){
        if(strcmp(il2cpp_method_get_name(m),name)||il2cpp_method_get_param_count(m)!=types.size())continue;
        bool ok=true;int i=0;for(auto wanted:types){char* got=il2cpp_type_get_name(il2cpp_method_get_param(m,i++));if(!got||strcmp(got,wanted))ok=false;if(got)il2cpp_free(got);}
        if(ok)return m;
    }return nullptr;
}
static P call(M m,P obj=nullptr,P* args=nullptr){
    if(!m)return nullptr;P exception=nullptr;P value=il2cpp_runtime_invoke(m,obj,args,&exception);
    if(exception){static int errors=0;if(errors++<12)LOG("Managed call failed: %s",il2cpp_method_get_name(m));return nullptr;}return value;
}
static P call(P o,const char* name,int n=0,P* args=nullptr){return o?call(method(il2cpp_object_get_class(o),name,n),o,args):nullptr;}
template<class T>static T value(P o,T fallback={}){return o?*static_cast<T*>(il2cpp_object_unbox(o)):fallback;}
template<class T>static T field(P o,const char* name){T result{};if(o)if(P f=il2cpp_class_get_field_from_name(il2cpp_object_get_class(o),name))il2cpp_field_get_value(o,f,&result);return result;}
template<class T>static void setfield(P o,const char* name,T v){if(o)if(P f=il2cpp_class_get_field_from_name(il2cpp_object_get_class(o),name))english::writeValueField(il2cpp_field_set_value,o,f,v);}
static void setreffield(P o,const char* name,P v){if(o)if(P f=il2cpp_class_get_field_from_name(il2cpp_object_get_class(o),name))english::writeObjectField(il2cpp_field_set_value_object,o,f,v);}
static P stat(const char* c,const char* name){P result=nullptr;P k=cls("",c);if(k)if(P f=il2cpp_class_get_field_from_name(k,name))il2cpp_field_static_get_value(f,&result);return result;}
static P type(P c){return c?il2cpp_type_get_object(il2cpp_class_get_type(c)):nullptr;}
static std::string ascii(P s){std::string result;if(s){const char16_t* ch=il2cpp_string_chars(s);for(int i=0;i<il2cpp_string_length(s);i++)result+=ch[i]<128?char(ch[i]):'?';}return result;}
static P str(const char* s){return il2cpp_string_new(s);}
static bool alive(P o){if(!o)return false;P args[]={o};return value<bool>(call(method(cls("UnityEngine","Object"),"op_Implicit",1),nullptr,args));}
static std::vector<P> array(P a){std::vector<P> r;if(a){uintptr_t n=il2cpp_array_length(a);if(n<100000){P* items=(P*)((char*)a+sizeof(P)*4);r.assign(items,items+n);}}return r;}
static P component(P go,P c){if(!go||!c)return nullptr;P args[]={type(c)};return call(overload(cls("UnityEngine","GameObject"),"GetComponent",{"System.Type"}),go,args);}
static std::vector<P> children(P go,P c){bool all=true;P args[]={type(c),&all};return array(call(overload(cls("UnityEngine","GameObject"),"GetComponentsInChildren",{"System.Type","System.Boolean"}),go,args));}
static void name(P o,const char* s){P args[]={str(s)};call(method(cls("UnityEngine","Object"),"set_name",1),o,args);}
static std::string name(P o){return ascii(call(method(cls("UnityEngine","Object"),"get_name",0),o));}
static P translated(P text){
    if(!text)return text;int n=il2cpp_string_length(text);if(n>16384)return text;
    const char16_t* ch=il2cpp_string_chars(text);bool cjk=false;for(int i=0;i<n;i++)if(ch[i]>=0x3400&&ch[i]<=0x9fff){cjk=true;break;}if(!cjk)return text;
    JNIEnv* e=env();if(!e)return text;
    jstring input=e->NewString((const jchar*)ch,n);jstring output=(jstring)e->CallStaticObjectMethod(bridge,translateJava,input);
    P result=text;if(e->ExceptionCheck()){e->ExceptionClear();}else if(output){const jchar* chars=e->GetStringChars(output,nullptr);int size=e->GetStringLength(output);if(size!=n||memcmp(chars,ch,size*sizeof(jchar)))result=il2cpp_string_new_utf16((const char16_t*)chars,size);e->ReleaseStringChars(output,chars);}
    if(output)e->DeleteLocalRef(output);e->DeleteLocalRef(input);return result;
}
static bool editable(P o){for(P c:{cls("TMPro","TMP_InputField"),cls("UnityEngine.UI","InputField")}){if(!c)continue;P args[]={type(c)};if(call(overload(cls("UnityEngine","Component"),"GetComponentInParent",{"System.Type"}),o,args))return true;}return false;}
static P parentComponent(P o,const char* ns,const char* className){
    P c=cls(ns,className);if(!c)return nullptr;P args[]={type(c)};
    return call(overload(cls("UnityEngine","Component"),"GetComponentInParent",{"System.Type"}),o,args);
}
static bool within(P o,const char* ns,const char* className){return parentComponent(o,ns,className)!=nullptr;}
static jstring javaString(JNIEnv* e,P s){return s?e->NewString((const jchar*)il2cpp_string_chars(s),il2cpp_string_length(s)):nullptr;}
static P onlineTitle(P o,P source){
    P button=parentComponent(o,"","CustomButton_enterGame");
    if(!button||field<P>(button,"levelName")!=o)return source;
    P id=field<P>(field<P>(button,"onlineLevelInfo"),"levelId");if(!id)return source;
    JNIEnv* e=env();if(!e||!onlineTitleJava)return source;
    jstring ji=javaString(e,id),js=javaString(e,source),out=(jstring)e->CallStaticObjectMethod(bridge,onlineTitleJava,ji,js);
    P result=source;if(e->ExceptionCheck())e->ExceptionClear();else if(out){const jchar* v=e->GetStringChars(out,nullptr);int n=e->GetStringLength(out);if(!source||n!=il2cpp_string_length(source)||memcmp(v,il2cpp_string_chars(source),n*sizeof(jchar)))result=il2cpp_string_new_utf16((const char16_t*)v,n);e->ReleaseStringChars(out,v);}
    if(out)e->DeleteLocalRef(out);if(js)e->DeleteLocalRef(js);if(ji)e->DeleteLocalRef(ji);return result;
}
static bool sameText(P text,const char16_t* expected){
    if(!text)return false;size_t n=std::char_traits<char16_t>::length(expected);
    return il2cpp_string_length(text)==n && !memcmp(il2cpp_string_chars(text),expected,n*sizeof(char16_t));
}
static bool editorToolButton(P o){
    // The editor builds its popup under a canvas. Resolve the live editor and
    // MakeButton clones RuntimeNodeUI.buttonPrefab (TheButton), not UIButton.
    // Require its toolWindow subtree and that exact component, rather than
    // changing every Disabled label in the editor or the game's settings.
    P k=cls("GameLevel.EventNodes","RuntimeEventNodeEditor"),editor=nullptr;
    if(k)if(P f=il2cpp_class_get_field_from_name(k,"Instance"))il2cpp_field_static_get_value(f,&editor);
    if(!alive(editor))return false;
    P window=field<P>(editor,"toolWindow");
    if(!alive(window)||!within(o,"","TheButton"))return false;
    P args[]={window};return value<bool>(call(call(o,"get_transform"),"IsChildOf",1,args));
}
static P displayText(P o,P source){
    // The source literal is shared with settings toggles. Only the creator help
    // window's standalone close label uses Close; Disabled remains valid elsewhere.
    if((sameText(source,u"Disabled")||sameText(source,u"关闭")) &&
       (within(o,"GameLevel.EventNodes","CreatorHelpWindow")||editorToolButton(o)))return str("Close");
    // PC RuntimeNodeUI uses contextual _code keys for these three port labels.
    // Apply only at render time; node values, IDs and editable inputs stay intact.
    if((sameText(source,u"阳光不足")||sameText(source,u"金币不足")||sameText(source,u"输出")) &&
       within(o,"GameLevel.EventNodes","RuntimeNodeUI")){
        std::u16string key(il2cpp_string_chars(source),il2cpp_string_length(source));key+=u"_code";
        P input=il2cpp_string_new_utf16(key.data(),key.size()),result=translated(input);
        if(result!=input)return result;
    }
    // Catalog names are identified by PC online IDs, never by editable filenames.
    if(source && il2cpp_string_length(source)<256){
        bool cjk=false;for(int i=0;i<il2cpp_string_length(source);i++){char16_t c=il2cpp_string_chars(source)[i];if(c>=0x3400&&c<=0x9fff){cjk=true;break;}}
        if(cjk){P title=onlineTitle(o,source);if(title!=source)return title;}
    }
    return translated(source);
}
using Event=void(*)(P,P,M);
using Tick=void(*)(P,M);
static Tick oldClick=nullptr;
static Tick oldUpdate=nullptr,oldInGameStart=nullptr,oldOptionStart=nullptr;
static Tick oldParse=nullptr;
static Event oldPopulate=nullptr;
static Event oldCustomAwake=nullptr;
static void customAwake(P o,P board,M m){
    // PC rewrites serialized level data. Instead register the current source
    // title/tip for rendering only, before the original displays its start tip.
    JNIEnv* e=env();P id=field<P>(o,"levelId");
    if(e&&registerOnlineJava&&id&&!field<bool>(o,"edit")){
        P data=call(o,"get_SerializedLevelData"),config=field<P>(data,"boardConfig");
        jstring ji=javaString(e,id),jn=javaString(e,field<P>(data,"name")),jt=javaString(e,field<P>(config,"startTip"));
        e->CallStaticVoidMethod(bridge,registerOnlineJava,ji,jn,jt);if(e->ExceptionCheck())e->ExceptionClear();
        if(ji)e->DeleteLocalRef(ji);if(jn)e->DeleteLocalRef(jn);if(jt)e->DeleteLocalRef(jt);
    }
    oldCustomAwake(o,board,m);
}
static void parseText(P o,M m){
    static bool first=true;if(first){first=false;LOG("Render callback reached");}
    // Translate the rendering input only, then restore the source text and input
    // mode. Code reading a puzzle label still receives its original resource key.
    if(editable(o)){oldParse(o,m);return;}
    P source=call(o,"get_text");P english=displayText(o,source);
    if(english==source){oldParse(o,m);return;}
    P original=field<P>(o,"m_text");int input=field<int>(o,"m_inputSource");
    setreffield(o,"m_text",english);setfield(o,"m_inputSource",3);
    oldParse(o,m);
    setreffield(o,"m_text",original);setfield(o,"m_inputSource",input);
    setfield(o,"m_IsTextBackingStringDirty",false);
}
static void populateText(P o,P helper,M m){
    if(editable(o)){oldPopulate(o,helper,m);return;}
    P original=field<P>(o,"m_Text");setreffield(o,"m_Text",displayText(o,original));oldPopulate(o,helper,m);setreffield(o,"m_Text",original);
}
struct V2{float x,y;};
struct V3{float x,y,z;};
static Tick oldAdventureRelease=nullptr;
static void adventureRelease(P o,M m){
    // Official 4.0.5 marks Challenge/MaLiang (197) as limInMobile.
    // Its modal rejection leaves Recommended Levels unresponsive on Android.
    // Replace only this rejected entry with the existing fading notification;
    // never lift the restriction or enter a mode whose AI service is absent.
    if(field<int>(o,"levelType")!=1 || field<int>(o,"buttonNumber")!=197 ||
       !field<bool>(o,"limInMobile")){
        oldAdventureRelease(o,m);return;
    }
    P rect=field<P>(o,"rectTransform");
    if(alive(rect)){
        V3 origin=field<V3>(o,"originPosition");V2 position={origin.x,origin.y};
        P args[]={&position};call(rect,"set_anchoredPosition",1,args);
    }
    P notice=call(method(cls("Core","InGameText"),"get_Instance",0));
    if(alive(notice)){
        float seconds=4.0f,y=-400.0f;bool cover=true;
        P args[]={str("Magic Plantbrush is not available on Android."),&seconds,&cover,&y};
        call(method(cls("Core","InGameText"),"ShowText",4),notice,args);
    }
    LOG("Magic Plantbrush mobile restriction shown without opening modal");
}
static uint32_t damageButton=0,damageTemplate=0,damageOwner=0,musicButton=0;
static bool musicAuditRequested=true;
static void release(uint32_t& h){if(h)il2cpp_gchandle_free(h);h=0;}
static P target(uint32_t h){return h?il2cpp_gchandle_get_target(h):nullptr;}
static void label(P go,const std::string& text){
    for(P t:children(go,cls("TMPro","TMP_Text"))){if(ascii(call(t,"get_text"))==text)continue;P args[]={str(text.c_str())};call(method(cls("TMPro","TMP_Text"),"set_text",1),t,args);bool yes=true;P a[]={&yes};call(t,"set_enableAutoSizing",1,a);float lo=10,hi=18;P b[]={&lo};call(t,"set_fontSizeMin",1,b);P c[]={&hi};call(t,"set_fontSizeMax",1,c);P rt=call(t,"get_rectTransform");V2 size={117,45};P dims[]={&size};call(rt,"set_sizeDelta",1,dims);}
}
static P newEvent(){P c=cls("UnityEngine.Events","UnityEvent");P o=il2cpp_object_new(c);call(method(c,".ctor",0),o);return o;}
static P cloneButton(P original,const char* id,const char* text,bool gameplay=false){
    if(!alive(original))return nullptr;
    P tr=call(original,"get_transform"),parent=call(tr,"get_parent");bool world=false;P args[]={original,parent,&world};
    int existingCount=value<int>(call(parent,"get_childCount"));
    for(int i=0;i<existingCount;i++){P a[]={&i};P child=call(parent,"GetChild",1,a);P go=call(child,"get_gameObject");if(name(go)==id)return go;}
    P go=call(overload(cls("UnityEngine","Object"),"Instantiate",{"UnityEngine.Object","UnityEngine.Transform","System.Boolean"}),nullptr,args);if(!go)return nullptr;
    name(go,id);P button=component(go,cls("","UIButton"));
    if(!button){P a[]={go};call(method(cls("UnityEngine","Object"),"Destroy",1),nullptr,a);return nullptr;}
    setreffield(button,"clickEvent",newEvent());
    if(gameplay){
        // The original bottom-up GridLayoutGroup owns position, size and order.
        // Start hidden even if the template was already enabled this frame.
        bool visible=false;P a[]={&visible};call(go,"SetActive",1,a);
        return go;
    }
    P rt=call(go,"get_transform");V3 pos=value<V3>(call(tr,"get_localPosition"));
    int count=value<int>(call(parent,"get_childCount"));float minY=pos.y;float height=40;
    V2 size=value<V2>(call(component(original,cls("UnityEngine","RectTransform")),"get_sizeDelta"));if(size.y>1)height=size.y;
    for(int i=0;i<count;i++){P a[]={&i};P child=call(parent,"GetChild",1,a);if(child==rt)continue;P cg=call(child,"get_gameObject");if(!value<bool>(call(cg,"get_activeSelf")))continue;V3 cp=value<V3>(call(child,"get_localPosition"));if(std::abs(cp.x-pos.x)<10)minY=std::min(minY,cp.y);}
    pos.y=minY-height-6;P a[]={&pos};call(rt,"set_localPosition",1,a);
    bool yes=true;P active[]={&yes};call(go,"SetActive",1,active);label(go,text);return go;
}
static void refreshDamage(){
    P b=target(damageButton);if(!alive(b))return;
    std::string text=field<bool>(stat("Board","Instance"),"showBulletDamage")?"Projectile Info\nOn":"Projectile Info\nOff";
    for(P t:children(b,cls("TMPro","TMP_Text"))){
        if(ascii(call(t,"get_text"))==text)continue;
        P a[]={str(text.c_str())};call(t,"set_text",1,a);
        bool yes=true,no=false;P autoSize[]={&yes},wrap[]={&no};
        call(t,"set_enableAutoSizing",1,autoSize);call(t,"set_enableWordWrapping",1,wrap);
        float lo=10,hi=14;P minSize[]={&lo},maxSize[]={&hi};
        call(t,"set_fontSizeMin",1,minSize);call(t,"set_fontSizeMax",1,maxSize);
        // Stretch within the button with an inset, rather than inheriting the
        // health label's single-line offset or imposing a screen-pixel position.
        P rt=call(t,"get_rectTransform");V2 zero={0,0},one={1,1},center={.5f,.5f},inset={-8,-8};
        P z[]={&zero},u[]={&one},p[]={&center},s[]={&inset};
        call(rt,"set_anchorMin",1,z);call(rt,"set_anchorMax",1,u);
        call(rt,"set_pivot",1,p);call(rt,"set_sizeDelta",1,s);call(rt,"set_anchoredPosition",1,z);
    }
}
static void syncDamageVisibility(){
    P b=target(damageButton),original=target(damageTemplate),owner=target(damageOwner);
    if(!alive(b))return;
    bool visible=alive(original)&&alive(owner)&&value<bool>(call(original,"get_activeSelf"));
    if(value<bool>(call(b,"get_activeSelf"))==visible)return;
    if(visible)refreshDamage();
    P a[]={&visible};call(b,"SetActive",1,a);
    if(visible){
        // InGameUI caches active colliders. Include ours without changing the
        // menu's current modal/pause interaction state.
        bool enabled=value<bool>(call(owner,"get_Interactable"));
        call(owner,"GetCol");P state[]={&enabled};call(owner,"set_Interactable",1,state);
    }
}
static void refreshMusic(){P b=target(musicButton);if(alive(b))label(b,blooms?"Music: Blooms":"Music: Original");}
static void click(P o,M m){
    P go=call(o,"get_gameObject");std::string id=name(go);
    if(id=="EnglishProjectileInfo") {
        P b=stat("Board","Instance");if(alive(b)){bool show=!field<bool>(b,"showBulletDamage");setfield(b,"showBulletDamage",show);if(show)setfield(stat("GameAPP","config"),"showBulletDamage",true);refreshDamage();}return;
    }
    if(id=="EnglishMusicSelector") {blooms=!blooms;musicAuditRequested=true;JNIEnv* e=env();if(e){e->CallStaticVoidMethod(bridge,saveMusicJava,jboolean(blooms));if(e->ExceptionCheck())e->ExceptionClear();}refreshMusic();return;}
    oldClick(o,m);
}
static void attachInGame(P o){
    release(damageButton);release(damageTemplate);release(damageOwner);
    P original=field<P>(o,"ShowPlantHealth");
    P go=cloneButton(original,"EnglishProjectileInfo","",true);
    if(go){damageButton=il2cpp_gchandle_new(go,false);damageTemplate=il2cpp_gchandle_new(original,false);damageOwner=il2cpp_gchandle_new(o,false);}
    refreshDamage();syncDamageVisibility();LOG("Projectile button: %s",go?"created, visibility follows health control":"template unavailable");
}
static void inGameStart(P o,M m){LOG("InGameUI Start callback reached");oldInGameStart(o,m);attachInGame(o);}
static void attachOptions(P o){
    release(musicButton);
    // This hierarchy is verified against the pinned Android prefab. Unity's
    // persistent-event inspection methods were stripped from this player.
    P findArgs[]={str("Buttons/Almanac")};
    P templateTransform=call(call(o,"get_transform"),"Find",1,findArgs);
    P templateGo=call(templateTransform,"get_gameObject");
    if(!component(templateGo,cls("","UIButton")))templateGo=nullptr;
    if(!templateGo){LOG("Music selector: verified template unavailable");return;}
    // Android's original F control calls SetResolution(1920,1080,...), which
    // distorts wide displays. Reuse its slot and deactivate that PC control.
    // Keep all other controls, captions and confirmation prompts untouched.
    P parent=call(templateTransform,"get_parent"),findScreen[]={str("F")};
    P slot=call(parent,"Find",1,findScreen),screenGo=call(slot,"get_gameObject");
    P screenButton=component(screenGo,cls("","OptionBtn"));
    if(!alive(screenGo)||!screenButton||field<int>(screenButton,"optionType")!=0){LOG("Music selector: verified screen-mode slot unavailable");return;}
    P go=cloneButton(templateGo,"EnglishMusicSelector",blooms?"Music: Blooms":"Music: Original");
    if(!go){LOG("Music selector: clone unavailable");return;}
    P tr=call(go,"get_transform");
    for(const char* property:{"anchorMin","anchorMax","pivot","sizeDelta"}){
        std::string getter=std::string("get_")+property,setter=std::string("set_")+property;
        V2 v=value<V2>(call(slot,getter.c_str()));P a[]={&v};call(tr,setter.c_str(),1,a);
    }
    V3 scale=value<V3>(call(slot,"get_localScale")),pos=value<V3>(call(slot,"get_localPosition"));
    P sa[]={&scale},pa[]={&pos};call(tr,"set_localScale",1,sa);call(tr,"set_localPosition",1,pa);
    setfield(component(go,cls("","UIButton")),"originPosition",pos);
    bool no=false;P off[]={&no};call(screenGo,"SetActive",1,off);
    musicButton=il2cpp_gchandle_new(go,false);bool enabled=value<bool>(call(o,"get_Interactable"));call(o,"GetCol");P a[]={&enabled};call(o,"set_Interactable",1,a);
    LOG("Music selector: created in screen-mode slot; desktop resolution control disabled");
}
static void optionStart(P o,M m){LOG("OptionMenu Start callback reached");oldOptionStart(o,m);attachOptions(o);}

// At most the currently requested tracks are decoded; do not preload 17 songs into RAM.
struct Track{std::string name;uint32_t original=0,request=0,replacement=0;bool failed=false;int unused=0;std::chrono::steady_clock::time_point started;};
static std::vector<Track> tracks;
struct MusicMute{uint32_t source=0;float previous=0;};
static MusicMute pendingMute[2];
static void (*oldVolume)(P,float,M)=nullptr;
static M volumeMethod=nullptr;
static void setVolume(P source,float volume,M m){
    // Preserve volume changes made by the game's settings during a load.
    // Every source except the two temporarily held music sources passes through.
    for(auto& state:pendingMute)if(state.source&&target(state.source)==source){state.previous=volume;oldVolume(source,0,m);return;}
    oldVolume(source,volume,m);
}
static void restoreMute(MusicMute& state){
    if(P source=target(state.source))if(alive(source)&&oldVolume)oldVolume(source,state.previous,volumeMethod);
    release(state.source);
}
static void holdMute(MusicMute& state,P source){
    if(!oldVolume)return;
    if(target(state.source)==source)return;
    restoreMute(state);
    if(alive(source)){state.previous=value<float>(call(source,"get_volume"));state.source=il2cpp_gchandle_new(source,false);oldVolume(source,0,volumeMethod);}
}
static const char* musicNames[]={"Boss2","Day_drum","Day","Fog_drum","Fog","Garden","IZ","MainMenu","Night_drum","Night","Pool_drum","Pool","Roof_drum","Roof_pre","Roof","SelectCard","UltimateBattle"};
static void auditMusic(){
    // Read-only diagnostic, once after a selection settles. Include other scene
    // sources too, so an unexpected duplicate music player would be visible.
    bool includeInactive=false;P args[]={type(cls("UnityEngine","AudioSource")),&includeInactive};
    M find=overload(cls("UnityEngine","Object"),"FindObjectsOfType",{"System.Type","System.Boolean"});
    P found=call(find,nullptr,args);
    if(!found){LOG("Music audit unavailable: scene enumeration failed");return;}
    auto sources=array(found);
    int playing=0,audible=0;LOG("Music audit begin: selection=%s",blooms?"Blooms":"Original");
    for(P source:sources){
        P clip=call(source,"get_clip");if(!alive(clip))continue;std::string clipName=name(clip);
        bool known=clipName.rfind("EnglishMusic_",0)==0;for(auto n:musicNames)if(clipName==n)known=true;if(!known)continue;
        bool active=value<bool>(call(source,"get_isPlaying"));float volume=value<float>(call(source,"get_volume"));float time=value<float>(call(source,"get_time"));
        if(active)playing++;if(active&&volume>0.0001f)audible++;
        LOG("Music source %p role=%s clip=%s playing=%d volume=%.3f time=%.2f",source,source==stat("GameAPP","music")?"main":source==stat("GameAPP","musicDrum")?"drum":"other",clipName.c_str(),active,volume,time);
    }
    LOG("Music audit end: scene sources=%zu, playing music=%d, nonzero-volume music=%d",sources.size(),playing,audible);
}
static void destroy(P o){if(o){P a[]={o};call(method(cls("UnityEngine","Object"),"Destroy",1),nullptr,a);}}
static void dispose(Track& t){if(P r=target(t.request)){call(r,"Abort");call(r,"Dispose");}release(t.request);destroy(target(t.replacement));release(t.replacement);release(t.original);}
static void switchClip(P source,P clip){
    bool playing=value<bool>(call(source,"get_isPlaying"));float time=value<float>(call(source,"get_time"));
    float duration=value<float>(call(clip,"get_length"));P a[]={clip};call(source,"set_clip",1,a);
    if(duration>0){time=std::min(time,std::max(0.f,duration-.05f));P b[]={&time};call(source,"set_time",1,b);}if(playing)call(source,"Play");
}
static void musicTick(){
    for(auto& t:tracks)t.unused++;
    int sourceIndex=0;
    for(const char* fieldName:{"music","musicDrum"}){
        MusicMute& mute=pendingMute[sourceIndex++];
        P source=stat("GameAPP",fieldName);if(!alive(source)){restoreMute(mute);continue;}P current=call(source,"get_clip");if(!alive(current)){restoreMute(mute);continue;}
        std::string clipName=name(current);Track* item=nullptr;
        for(auto& t:tracks)if(target(t.original)==current||target(t.replacement)==current){item=&t;break;}
        if(!item){bool supported=false;for(auto n:musicNames)if(clipName==n)supported=true;if(!supported){restoreMute(mute);continue;}Track t;t.name=clipName;t.original=il2cpp_gchandle_new(current,false);tracks.push_back(t);item=&tracks.back();}
        Track& t=*item;t.unused=0;
        if(!blooms){P orig=target(t.original);if(current!=orig)switchClip(source,orig);restoreMute(mute);continue;}
        if(!t.failed&&!t.replacement)holdMute(mute,source);
        if(!t.request&&!t.replacement&&!t.failed){
            std::string ext=(t.name=="MainMenu"||t.name=="Garden")?".ogg":".mp3";
            int audioType=ext==".ogg"?14:13;std::string path="file://"+runtimeRoot+"/"+t.name+ext;
            P a[]={str(path.c_str()),&audioType};P req=call(method(cls("UnityEngine.Networking","UnityWebRequestMultimedia"),"GetAudioClip",2),nullptr,a);
            if(req){t.request=il2cpp_gchandle_new(req,false);t.started=std::chrono::steady_clock::now();int timeout=15;P limit[]={&timeout};call(req,"set_timeout",1,limit);P handler=call(req,"get_downloadHandler");bool stream=true;P b[]={&stream};call(handler,"set_streamAudio",1,b);call(req,"SendWebRequest");}else t.failed=true;
        }
        if(t.request&&std::chrono::steady_clock::now()-t.started>std::chrono::seconds(15)){P req=target(t.request);call(req,"Abort");call(req,"Dispose");release(t.request);t.failed=true;LOG("Music load timed out: %s",t.name.c_str());}
        if(P req=target(t.request))if(value<bool>(call(req,"get_isDone"))){
            if(value<int>(call(req,"get_result"))==1){P a[]={req};P clip=call(method(cls("UnityEngine.Networking","DownloadHandlerAudioClip"),"GetContent",1),nullptr,a);if(clip){t.replacement=il2cpp_gchandle_new(clip,false);name(clip,("EnglishMusic_"+t.name).c_str());}else t.failed=true;}else t.failed=true;
            call(req,"Dispose");release(t.request);if(t.failed)LOG("Music fallback: %s",t.name.c_str());
        }
        if(P replacement=target(t.replacement))if(replacement!=current)switchClip(source,replacement);
        if(t.replacement||t.failed)restoreMute(mute);
    }
    for(auto it=tracks.begin();it!=tracks.end();)if(it->unused>4){dispose(*it);it=tracks.erase(it);}else ++it;
    if(musicAuditRequested&&!tracks.empty()&&std::none_of(tracks.begin(),tracks.end(),[](const Track& t){return t.request!=0;})){musicAuditRequested=false;auditMusic();}
}
static void (*oldPlayMusic)(P,int,M)=nullptr;
static void playMusic(P o,int id,M m){
    // Silence only the two game music sources before original PlayMusic starts
    // a track. Sound effects and the user's music volume are preserved. This
    // Android player strips AudioSource.mute, so retain volume through its setter.
    if(blooms){holdMute(pendingMute[0],stat("GameAPP","music"));holdMute(pendingMute[1],stat("GameAPP","musicDrum"));}
    oldPlayMusic(o,id,m);musicTick();
}
static void scanInitialText(){
    for(P c:{cls("TMPro","TMP_Text"),cls("UnityEngine.UI","Text")}){
        P a[]={type(c)};auto objects=array(call(overload(cls("UnityEngine","Object"),"FindObjectsOfType",{"System.Type"}),nullptr,a));
        for(P t:objects)call(t,"SetAllDirty");
    }
    // A menu may have completed Start while the native bridge was loading.
    // Find scene instances (including hidden menus), never prefab assets.
    if(oldClick){
        bool inactive=true;
        for(const char* c:{"InGameUI","OptionMenu"}){
            P a[]={type(cls("",c)),&inactive};
            auto objects=array(call(overload(cls("UnityEngine","Object"),"FindObjectsOfType",{"System.Type","System.Boolean"}),nullptr,a));
            for(P o:objects){if(!strcmp(c,"InGameUI"))attachInGame(o);else attachOptions(o);}
        }
    }
}
static void update(P o,M m){
    static bool first=true;if(first){first=false;LOG("GameAPP Update callback reached");}
    oldUpdate(o,m);static bool initial=true;if(initial){initial=false;scanInitialText();}
    syncDamageVisibility();
    static auto last=std::chrono::steady_clock::now();auto now=std::chrono::steady_clock::now();if(now-last<std::chrono::milliseconds(250))return;last=now;
    musicTick();refreshDamage();
}
static bool hook(P c,const char* name,int count,P replacement,P* original){M m=method(c,name,count);if(!m||!*(P*)m){LOG("Missing hook %s",name);return false;}Dl_info info{};dladdr(*(P*)m,&info);LOG("Target %s: RVA=%llx next=%p",name,(unsigned long long)((uintptr_t)*(P*)m-(uintptr_t)info.dli_fbase),((P*)m)[1]);int result=DobbyHook(*(P*)m,replacement,original);LOG("Hook %s: %d",name,result);return result==0;}
static bool bind(P lib){
#define LOAD(name) name=reinterpret_cast<decltype(name)>(dlsym(lib,#name));if(!name){LOG("Missing API %s",#name);return false;}
    LOAD(il2cpp_domain_get) LOAD(il2cpp_domain_get_assemblies) LOAD(il2cpp_assembly_get_image)
    LOAD(il2cpp_class_from_name) LOAD(il2cpp_class_get_method_from_name) LOAD(il2cpp_class_get_methods)
    LOAD(il2cpp_method_get_name) LOAD(il2cpp_method_get_param_count) LOAD(il2cpp_method_get_param)
    LOAD(il2cpp_type_get_name) LOAD(il2cpp_free) LOAD(il2cpp_class_get_type) LOAD(il2cpp_type_get_object)
    LOAD(il2cpp_object_get_class) LOAD(il2cpp_class_get_field_from_name) LOAD(il2cpp_field_get_value)
    LOAD(il2cpp_field_set_value) LOAD(il2cpp_field_set_value_object) LOAD(il2cpp_field_static_get_value) LOAD(il2cpp_runtime_invoke)
    LOAD(il2cpp_object_unbox) LOAD(il2cpp_object_new) LOAD(il2cpp_string_new) LOAD(il2cpp_string_new_utf16)
    LOAD(il2cpp_string_chars) LOAD(il2cpp_string_length) LOAD(il2cpp_gchandle_new) LOAD(il2cpp_gchandle_get_target)
    LOAD(il2cpp_gchandle_free) LOAD(il2cpp_array_length) LOAD(il2cpp_thread_attach) LOAD(il2cpp_thread_detach)
#undef LOAD
    return true;
}
static void initialize(){
    // Called on Unity's already-attached thread only AFTER il2cpp_init succeeds.
    // Published assemblies are not proof that the VM's thread system is ready.
    // Resolve once before hooks are installed. The version-specific APK builder checks native hashes.
    if(!cls("","GameAPP")||!cls("","UIButton")||!cls("TMPro","TMP_Text")){LOG("Unexpected game schema; runtime disabled");return;}
    hook(cls("TMPro","TMP_Text"),"ParseInputText",0,(P)parseText,(P*)&oldParse);
    hook(cls("GameLevel","CustomLevelData"),"OnBoardAwake",1,(P)customAwake,(P*)&oldCustomAwake);
    hook(cls("UnityEngine.UI","Text"),"OnPopulateMesh",1,(P)populateText,(P*)&oldPopulate);
    if(hook(cls("","UIButton"),"OnClicked",0,(P)click,(P*)&oldClick)){
        hook(cls("","InGameUI"),"Start",0,(P)inGameStart,(P*)&oldInGameStart);
        hook(cls("","OptionMenu"),"Start",0,(P)optionStart,(P*)&oldOptionStart);
    }
    hook(cls("","GameAPP"),"Update",0,(P)update,(P*)&oldUpdate);
    // Resolve by class/method names on both ABIs, never by disassembly offsets.
    if(method(cls("Core","InGameText"),"get_Instance",0) &&
       overload(cls("Core","InGameText"),"ShowText",{"System.String","System.Single","System.Boolean","System.Single"}))
        hook(cls("","Advanture_Btn"),"OnMouseUp",0,(P)adventureRelease,(P*)&oldAdventureRelease);
    volumeMethod=method(cls("UnityEngine","AudioSource"),"set_volume",1);
    hook(cls("UnityEngine","AudioSource"),"set_volume",1,(P)setVolume,(P*)&oldVolume);
    hook(cls("","GameAPP"),"PlayMusic",1,(P)playMusic,(P*)&oldPlayMusic);
    LOG("Runtime initialization finished after IL2CPP init");
}
static std::once_flag ready;
static int (*originalInit)(const char*)=nullptr;
static int (*originalInit16)(const char16_t*)=nullptr;
static int runtimeInit(const char* domain){int result=originalInit(domain);if(result)std::call_once(ready,initialize);return result;}
static int runtimeInit16(const char16_t* domain){int result=originalInit16(domain);if(result)std::call_once(ready,initialize);return result;}
extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* v,P){vm=v;return JNI_VERSION_1_6;}
extern "C" JNIEXPORT void JNICALL Java_com_silvershadow_pvzf_EnglishActivity_startRuntime(JNIEnv* e,jclass c,jstring root,jboolean useBlooms){
    static std::once_flag started;
    std::call_once(started,[&]{
    bridge=(jclass)e->NewGlobalRef(c);translateJava=e->GetStaticMethodID(c,"translate","(Ljava/lang/String;)Ljava/lang/String;");saveMusicJava=e->GetStaticMethodID(c,"saveMusic","(Z)V");
    onlineTitleJava=e->GetStaticMethodID(c,"onlineTitle","(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
    registerOnlineJava=e->GetStaticMethodID(c,"registerOnlineLevel","(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V");
    const char* path=e->GetStringUTFChars(root,nullptr);runtimeRoot=path;e->ReleaseStringUTFChars(root,path);blooms=useBlooms;
    P lib=dlopen("libil2cpp.so",RTLD_NOW|RTLD_NOLOAD);
    if(!lib||!bind(lib)||DobbyHook(dlsym(lib,"il2cpp_init"),(P)runtimeInit,(P*)&originalInit)!=0||DobbyHook(dlsym(lib,"il2cpp_init_utf16"),(P)runtimeInit16,(P*)&originalInit16)!=0){
        e->ThrowNew(e->FindClass("java/lang/IllegalStateException"),"Cannot install safe IL2CPP initialization hook");return;
    }
    LOG("IL2CPP completion hooks installed before Unity startup");
    });
}
