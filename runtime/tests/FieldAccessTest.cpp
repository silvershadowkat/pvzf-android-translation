#include "../field_access.h"
#include <cassert>
#include <cstring>
#include <iostream>

struct ManagedString { const char16_t* chars; };
struct Vector { float x,y,z; };
struct Object { void* reference; bool flag; int input; Vector position; };
struct Field { size_t offset; size_t size; };
static int values=0,references=0;

// Model the independently disassembled 4.0.5 ABI: reference setter stores its
// third argument directly; value setter copies bytes from the third argument.
static void setObject(void* object,void* info,void* value) {
    ++references;
    *reinterpret_cast<void**>(static_cast<char*>(object)+static_cast<Field*>(info)->offset)=value;
}
static void setValue(void* object,void* info,void* value) {
    ++values;auto f=static_cast<Field*>(info);
    std::memcpy(static_cast<char*>(object)+f->offset,value,f->size);
}
int main() {
    Object o{};ManagedString source{u"木桩"},translated{u"Training Dummy"};
    Field ref{offsetof(Object,reference),sizeof(void*)};
    Field flag{offsetof(Object,flag),sizeof(bool)},input{offsetof(Object,input),sizeof(int)};
    Field pos{offsetof(Object,position),sizeof(Vector)};
    english::writeObjectField(setObject,&o,&ref,&source);
    void* saved=o.reference;
    english::writeObjectField(setObject,&o,&ref,&translated);
    assert(o.reference==&translated);
    assert(static_cast<ManagedString*>(o.reference)->chars[13]==u'y');
    english::writeObjectField(setObject,&o,&ref,saved);
    assert(o.reference==&source);
    english::writeObjectField(setObject,&o,&ref,nullptr);
    assert(!o.reference);
    // UnityEvent uses the same reference ABI as TMP/legacy string fields.
    Object event{};english::writeObjectField(setObject,&o,&ref,&event);
    assert(o.reference==&event);
    english::writeValueField(setValue,&o,&flag,true);
    english::writeValueField(setValue,&o,&input,3);
    english::writeValueField(setValue,&o,&pos,Vector{1.0f,2.0f,3.0f});
    assert(o.flag && o.input==3 && o.position.x==1.0f && o.position.y==2.0f && o.position.z==3.0f);
    assert(values==3 && references==5);
#ifdef EXPECT_POINTER_REJECTION
    english::writeValueField(setValue,&o,&ref,&translated);
#endif
    std::cout << "Field ABI regression checks passed\n";
}
