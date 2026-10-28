#include "../display_cache.h"
#include <cassert>
#include <set>
#include <iostream>
int main(){
    using namespace english;
    assert(!displayCandidate(nullptr,0));assert(!displayCandidate(u"HP 123 / 400",12));
    assert(!displayCandidate(u"Player",6));assert(displayCandidate(u"Disabled",8));
    assert(displayCandidate(u"金币 12",5));assert(!displayCandidate(u"",0));
    DisplayCache c(48,2);std::set<uint32_t> freed;
    auto release=[&](uint32_t h){if(h){assert(!freed.count(h));freed.insert(h);}};
    uint32_t h=99;c.put(u"first",1,20,release);c.put(u"unchanged",0,20,release);
    assert(c.get(u"unchanged",h)&&h==0);assert(c.get(u"first",h)&&h==1);
    c.put(u"third",3,20,release);assert(!c.get(u"unchanged",h));assert(c.size()==2&&c.bytes()==40);
    c.put(u"fourth",4,40,release);assert(freed.count(1)&&freed.count(3));assert(c.size()==1);
    c.put(u"fourth",5,20,release);assert(freed.count(4));assert(c.get(u"fourth",h)&&h==5);
    c.put(u"too big",6,49,release);assert(freed.count(6)&&c.size()==1);
    c.clear(release);assert(freed.count(5)&&c.size()==0&&c.bytes()==0);
    assert(!c.get(u"fourth",h)); // online-level registration invalidates old results
    std::cout<<"Display gate, LRU recency, negative caching, byte/count limits, handle release and invalidation passed\n";
}
