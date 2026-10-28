#pragma once
#include <cstdint>
#include <string>
#include <list>
#include <unordered_map>
namespace english {
inline bool displayCandidate(const char16_t* text, int n) {
    if(!text || n<=0)return false;
    if(n==8 && std::char_traits<char16_t>::compare(text,u"Disabled",8)==0)return true;
    for(int i=0;i<n;++i)if(text[i]>=0x3400&&text[i]<=0x9fff)return true;
    return false;
}
// Bounded source-content LRU. Values are strong IL2CPP GC handles, or zero for
// an unchanged result. Never retain unrooted managed pointers across frames.
class DisplayCache {
    struct Entry {uint32_t handle;size_t bytes;std::list<std::u16string>::iterator age;};
    std::unordered_map<std::u16string,Entry> entries;
    std::list<std::u16string> ages;
    size_t used=0,limit,count;
public:
    explicit DisplayCache(size_t bytes=1024*1024,size_t items=1024):limit(bytes),count(items){}
    size_t maxBytes() const{return limit;}
    size_t size() const{return entries.size();}
    size_t bytes() const{return used;}
    bool get(const std::u16string& key,uint32_t& handle){
        auto it=entries.find(key);if(it==entries.end())return false;
        ages.splice(ages.begin(),ages,it->second.age);handle=it->second.handle;return true;
    }
    template<class Free>void clear(Free release){
        for(auto& row:entries)release(row.second.handle);
        entries.clear();ages.clear();used=0;
    }
    template<class Free>void put(std::u16string key,uint32_t handle,size_t cost,Free release){
        if(cost>limit||count==0){release(handle);return;}
        auto old=entries.find(key);
        if(old!=entries.end()){used-=old->second.bytes;release(old->second.handle);ages.erase(old->second.age);entries.erase(old);}
        while(!ages.empty()&&(entries.size()>=count||used+cost>limit)){
            auto it=entries.find(ages.back());used-=it->second.bytes;release(it->second.handle);entries.erase(it);ages.pop_back();
        }
        ages.push_front(key);entries.emplace(std::move(key),Entry{handle,cost,ages.begin()});used+=cost;
    }
};
}
