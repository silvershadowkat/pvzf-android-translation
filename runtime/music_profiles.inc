// Both profiles use Android-encoded streaming AudioClips in the game's own
// ResourceManager. No additional player, playback clock, polling or silent song.
// Profile selection is fixed until restart. Only the two game music sources
// are redirected; sound effects and unknown/new tracks pass through unchanged.
static void (*oldSetMusicClip)(P,P,M)=nullptr;
static void (*oldProfilePlayMusic)(P,int,M)=nullptr;
static P musicSources[2]={nullptr,nullptr};
static uint32_t musicSourceHandles[2]={0,0};
static void profilePlayMusic(P o,int id,M m){
    int i=0;
    for(const char* fieldName:{"music","musicDrum"}){
        P source=stat("GameAPP",fieldName);
        if(source!=musicSources[i]){
            release(musicSourceHandles[i]);musicSources[i]=source;
            if(source)musicSourceHandles[i]=il2cpp_gchandle_new(source,false);
        }
        ++i;
    }
    oldProfilePlayMusic(o,id,m);
}
static P profileClip(P original){
    std::string track=name(original);
    if(track.empty()||track.size()>64||!std::all_of(track.begin(),track.end(),[](unsigned char c){
        return (c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_';
    }))return original;
    std::transform(track.begin(),track.end(),track.begin(),[](unsigned char c){return c>='A'&&c<='Z'?c+32:c;});
    static std::unordered_map<std::string,uint32_t> cache;
    std::string key=std::string(blooms?"blooms/":"original/")+track;
    auto found=cache.find(key);
    if(found!=cache.end())return alive(target(found->second))?target(found->second):original;
    if(cache.size()>=64)return original;
    P audio=cls("UnityEngine","AudioClip");
    M load=overload(cls("UnityEngine","Resources"),"Load",{"System.String","System.Type"});
    if(!audio||!load)return original;
    auto loadProfile=[&](const std::string& path){
        P args[]={str(path.c_str()),il2cpp_type_get_object(il2cpp_class_get_type(audio))};
        return call(load,nullptr,args);
    };
    P selected=loadProfile("englishmusic/"+key);
    // Tracks without a reviewed Blooms replacement keep the normalized original,
    // including new 4.1 boss music. Missing assets retain the official track.
    if(!alive(selected)&&blooms)selected=loadProfile("englishmusic/original/"+track);
    if(!alive(selected)){
        LOG("Music resource unavailable; retaining official clip: %s",key.c_str());
        selected=original;
    }else LOG("Music streaming resource loaded: %s",key.c_str());
    cache[key]=il2cpp_gchandle_new(selected,false);
    return selected;
}
static void setMusicClip(P source,P clip,M m){
    // SFX assignments take only pointer comparisons. No reflection, Unity API,
    // string inspection or resource lookup is added to their hot path.
    if(source&&(source==musicSources[0]||source==musicSources[1])&&alive(clip))
        clip=profileClip(clip);
    oldSetMusicClip(source,clip,m);
}
