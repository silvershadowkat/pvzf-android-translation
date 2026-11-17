#include <string>
#include <initializer_list>
#include <cassert>
#include <cstdio>
using P=void*;using M=const void*;
#define LOG(...) ((void)0)
struct Box{P klass;int value;};
static P il2cpp_object_get_class(P p){return static_cast<Box*>(p)->klass;}
static P il2cpp_object_unbox(P p){return &static_cast<Box*>(p)->value;}
static bool sameText(P p,const char16_t* s){return p&&*static_cast<std::u16string*>(p)==s;}
static std::u16string fallback;
static P str(const char* text){fallback.clear();for(const char* p=text;*p;p++)fallback.push_back(*p);return &fallback;}
static P cls(const char*,const char*){return nullptr;}static P fieldInfo(P,const char*){return nullptr;}static M overload(P,const char*,std::initializer_list<const char*>){return nullptr;}static bool hook(P,const char*,int,P,P*){return false;}
#include "../modifier_display.inc"
static P result;static int calls;
static P nativeText(P,P,M){calls++;return result;}
int main(){
 oldModifierText=nativeText;modifierUltiClass=(P)1;Box missing{(P)1,52},otherId{(P)1,53},otherType{(P)2,52};
 std::u16string unknown=u"Unknown Modifier ID",chinese=u"未知索引",known=u"Existing native description";
 result=&unknown;assert(modifierText(nullptr,&missing,nullptr)==&fallback&&fallback.find(u"Obsidian Formation:")==0);
 result=&chinese;assert(modifierText(nullptr,&missing,nullptr)==&fallback);
 result=&unknown;assert(modifierText(nullptr,&otherId,nullptr)==result);assert(modifierText(nullptr,&otherType,nullptr)==result);assert(modifierText(nullptr,nullptr,nullptr)==result);
 result=&known;assert(modifierText(nullptr,&missing,nullptr)==result);assert(calls==6);
 puts("6 scoped modifier display checks passed; valid native results and other IDs retained.");
}
