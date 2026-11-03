// Both profiles use the original game's DecompressOnLoad AudioClip behavior.
// No additional player, playback clock, polling or silent song. Only the current
// music pair retains decoded PCM; inactive profile data is unloaded on changes.
// Profile selection is fixed until restart. Only the two game music sources
// are redirected; sound effects and unknown/new tracks pass through unchanged.
static void (*oldSetMusicClip)(P,P,M)=nullptr;
static void (*oldProfilePlayMusic)(P,int,M)=nullptr;
static P musicSources[2]={nullptr,nullptr};
static uint32_t musicSourceHandles[2]={0,0};
static std::unordered_map<std::string,uint32_t> musicClipCache;
static uint32_t musicCleanup=0;
static bool musicCleanupNeeded=false;
static void trimProfileAudio(){
    P active[2]={call(musicSources[0],"get_clip"),call(musicSources[1],"get_clip")};
    unsigned retired=0;
    for(auto it=musicClipCache.begin();it!=musicClipCache.end();){
        P clip=target(it->second);
        if(clip!=active[0]&&clip!=active[1]){
            il2cpp_gchandle_free(it->second);it=musicClipCache.erase(it);++retired;
        }else ++it;
    }
    if(retired){
        musicCleanupNeeded=true;
        LOG("Decoded music: released %u inactive references; %zu current clips",retired,musicClipCache.size());
    }
    // The per-clip unload API is stripped in official 4.1. Use its available
    // public asynchronous asset cleanup only after a real track retirement.
    // No cleanup on ordinary frames, no overlapping jobs, no broad file wipe.
    P pending=target(musicCleanup);
    if(pending&&!value<bool>(call(pending,"get_isDone")))return;
    release(musicCleanup);
    if(musicCleanupNeeded){
        P job=call(method(cls("UnityEngine","Resources"),"UnloadUnusedAssets",0));
        if(job)musicCleanup=il2cpp_gchandle_new(job,false);
        musicCleanupNeeded=false;
    }
}
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
    trimProfileAudio();
}
static P profileClip(P original){
#ifdef PVZF_MUSIC_DIAGNOSTICS
    // Local diagnostic Original is a true factory-audio control group.
    if(!blooms)return original;
#endif
    std::string track=name(original);
    if(track.empty()||track.size()>64||!std::all_of(track.begin(),track.end(),[](unsigned char c){
        return (c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_';
    }))return original;
    std::transform(track.begin(),track.end(),track.begin(),[](unsigned char c){return c>='A'&&c<='Z'?c+32:c;});
    std::string key=std::string(blooms?"blooms/":"original/")+track;
    auto found=musicClipCache.find(key);
    if(found!=musicClipCache.end()){
        P clip=target(found->second);
        if(alive(clip))return clip;
        // Scene cleanup may invalidate an asset. Reload the selected profile
        // instead of silently switching its next use to factory audio.
        il2cpp_gchandle_free(found->second);musicClipCache.erase(found);
    }
    if(musicClipCache.size()>=64)return original;
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
        return original;
    }else {
        LOG("Music decompressed resource loaded: %s",key.c_str());
        call(selected,"LoadAudioData");
    }
    musicClipCache[key]=il2cpp_gchandle_new(selected,false);
    return selected;
}
static void setMusicClip(P source,P clip,M m){
    // SFX assignments take only pointer comparisons. No reflection, Unity API,
    // string inspection or resource lookup is added to their hot path.
    if(source&&(source==musicSources[0]||source==musicSources[1])&&alive(clip))
        clip=profileClip(clip);
    oldSetMusicClip(source,clip,m);
}

#ifdef PVZF_MUSIC_DIAGNOSTICS
// Local A/B measurement only. Not installed in normal builds.
static void (*oldAuditSetTime)(P,float,M)=nullptr;
static unsigned auditSeeks=0;
static long long auditSeekMicros=0,auditMaxSeekMicros=0;
static unsigned auditFrames=0,auditSlowFrames=0;
static long long auditMaxFrameMicros=0;
static void musicAuditFrame(){
    static auto last=std::chrono::steady_clock::now();auto now=std::chrono::steady_clock::now();
    auto us=std::chrono::duration_cast<std::chrono::microseconds>(now-last).count();last=now;
    ++auditFrames;if(us>50000)++auditSlowFrames;auditMaxFrameMicros=std::max(auditMaxFrameMicros,(long long)us);
}
static void auditSetTime(P source,float seconds,M m){
    if(source!=musicSources[0]&&source!=musicSources[1]){oldAuditSetTime(source,seconds,m);return;}
    auto begin=std::chrono::steady_clock::now();oldAuditSetTime(source,seconds,m);
    auto us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-begin).count();
    ++auditSeeks;auditSeekMicros+=us;auditMaxSeekMicros=std::max(auditMaxSeekMicros,(long long)us);
}
static void musicAuditTick(){
    static auto start=std::chrono::steady_clock::now();auto now=std::chrono::steady_clock::now();
    if(now-start<std::chrono::seconds(10))return;
    LOG("Audio audit 10s: seeks=%u total_us=%lld max_us=%lld",auditSeeks,auditSeekMicros,auditMaxSeekMicros);
    LOG("Frame audit 10s: frames=%u over50ms=%u max_us=%lld",auditFrames,auditSlowFrames,auditMaxFrameMicros);
    auditSeeks=0;auditSeekMicros=0;auditMaxSeekMicros=0;start=now;
    auditFrames=0;auditSlowFrames=0;auditMaxFrameMicros=0;
}
#endif
