// Compiled into ENAI only. No server fallback or global string substitution.
static jmethodID offlineRequestJava=nullptr,offlineStatusJava=nullptr;
static Tick oldOfflineEnter=nullptr,oldOfflineParse=nullptr,oldOfflineStop=nullptr,oldOfflineExit=nullptr;
static Tick oldOfflineDispose=nullptr;
static uint32_t offlinePending=0;
static M offlinePendingMethod=nullptr;
static bool offlineReady=false;
static void offlineCancel(){if(offlinePending)il2cpp_gchandle_free(offlinePending);offlinePending=0;offlinePendingMethod=nullptr;}
static void offlineNotice(const char* text){
    P notice=call(method(cls("Core","InGameText"),"get_Instance",0));
    if(alive(notice)){float seconds=4.0f,y=-400.0f;bool cover=true;P args[]={str(text),&seconds,&cover,&y};call(method(cls("Core","InGameText"),"ShowText",4),notice,args);}
}
static int offlineState(bool request){
    JNIEnv* e=env();if(!e||!offlineReady)return -1;
    int state=e->CallStaticIntMethod(bridge,request?offlineRequestJava:offlineStatusJava);
    if(e->ExceptionCheck()){e->ExceptionClear();return -1;}return state;
}
// 4.1 Begin appends /recognize itself; the accessor must return the root.
static P offlineEndpoint(M){return str("http://127.0.0.1:17861");}
static void offlineEnter(P o,M m){offlineState(true);oldOfflineEnter(o,m);}
static void offlineParse(P o,M m){
    int state=offlineState(true);
    if(state==2){offlineCancel();oldOfflineParse(o,m);return;}
    if(state==1){offlineCancel();offlinePending=il2cpp_gchandle_new(o,false);offlinePendingMethod=m;offlineNotice("Loading offline recognition. Your drawing will be identified when ready.");}
    else offlineNotice("Offline recognition stopped. Wait a moment, then tap Identify to reload it.");
}
static void offlineStop(P o,M m){if(offlinePending&&il2cpp_gchandle_get_target(offlinePending)==o)offlineCancel();oldOfflineStop(o,m);}
static void offlineExit(P o,M m){
    offlineCancel();oldOfflineExit(o,m);
}
static void offlineDispose(P o,M m){
    offlineCancel();oldOfflineDispose(o,m);
}
static void offlinePendingTick(){
    if(!offlinePending)return;
    P menu=il2cpp_gchandle_get_target(offlinePending);
    if(!alive(menu)){offlineCancel();return;}
    int state=offlineState(false);if(state==1)return;
    M m=offlinePendingMethod;offlineCancel();
    if(state==2)oldOfflineParse(menu,m);else offlineNotice("Offline recognition was released. Tap Identify to load it again.");
}
static void initializeOffline(){
    // Install the loopback route first. If a later hook fails, fail closed at
    // the local endpoint instead of silently sending a drawing to the server.
    P request=cls("","MaLiangLocalRequest"),menu=cls("","MaLiangMenu");
    if(!hook(request,"get_endpoint",0,(P)offlineEndpoint,nullptr)){LOG("ENAI loopback hook unavailable");return;}
    M configure=method(request,"ConfigureEndpoint",2);
    if(!configure){LOG("ENAI configuration method unavailable");return;}
    P args[]={str("http://127.0.0.1:17861"),str("offline-local")};call(configure,nullptr,args);
    JNIEnv* e=env();if(!e)return;
    offlineRequestJava=e->GetStaticMethodID(bridge,"requestPlantbrush","()I");
    offlineStatusJava=e->GetStaticMethodID(bridge,"plantbrushStatus","()I");
    if(e->ExceptionCheck()){e->ExceptionClear();return;}
    offlineReady=offlineRequestJava&&offlineStatusJava;
    if(!offlineReady)return;
    bool ok=hook(menu,"Parse",0,(P)offlineParse,(P*)&oldOfflineParse);
    ok=hook(menu,"StopRequest",0,(P)offlineStop,(P*)&oldOfflineStop)&&ok;
    ok=hook(menu,"OnExit",0,(P)offlineExit,(P*)&oldOfflineExit)&&ok;
    ok=hook(menu,"Start",0,(P)offlineEnter,(P*)&oldOfflineEnter)&&ok;
    ok=hook(cls("GameLevel","MaLiangLevelData"),"Dispose",0,(P)offlineDispose,(P*)&oldOfflineDispose)&&ok;
    if(!ok){offlineReady=false;LOG("ENAI lifecycle hook unavailable; no online fallback");}
    else LOG("ENAI loopback recognition hooks installed; server route disabled");
}
