// Experimental 4.1 startup probe. Included only by build_startup_probe.py, never normal runtime builds.
#include <cstdio>
#include <cstdint>
using BenchClock=std::chrono::steady_clock;
static bool benchLoading=false;
static BenchClock::time_point benchInit;
static long long benchUs(BenchClock::time_point start){return std::chrono::duration_cast<std::chrono::microseconds>(BenchClock::now()-start).count();}
#define BLOG(...) __android_log_print(ANDROID_LOG_INFO,"PvZFStartup",__VA_ARGS__)
#define BENCH_STAGE(symbol,klass,label) static void (*symbol##Old)(P,M)=nullptr; static void symbol(P o,M m){auto b=BenchClock::now();BLOG("BEGIN %s",label);symbol##Old(o,m);BLOG("END %s us=%lld",label,benchUs(b));}
#define BENCH_STATIC(symbol,klass,label) static void (*symbol##Old)(M)=nullptr; static void symbol(M m){auto b=BenchClock::now();BLOG("BEGIN %s",label);symbol##Old(m);BLOG("END %s us=%lld",label,benchUs(b));}
BENCH_STAGE(benchResources,"ResourcesManager","ResourcesManager.ctor")
BENCH_STAGE(benchPlants,"ResourcesManager","ResourcesManager.LoadPlant")
BENCH_STAGE(benchNormalSkin,"ResourcesManager","ResourcesManager.LoadNormalSkin")
BENCH_STAGE(benchSkin,"ResourcesManager","ResourcesManager.LoadSkin")
BENCH_STAGE(benchBullets,"ResourcesManager","ResourcesManager.LoadBullet")
BENCH_STAGE(benchGrid,"ResourcesManager","ResourcesManager.LoadGridItem")
BENCH_STAGE(benchGameResources,"GameAPP","GameAPP.LoadResources")
BENCH_STAGE(benchSounds,"SoundManager","SoundManager.LoadSound")
BENCH_STAGE(benchMusic,"SoundManager","SoundManager.LoadMusic")
BENCH_STATIC(benchParticles,"GameAPP","GameAPP.LoadParticle")
BENCH_STATIC(benchItems,"GameAPP","GameAPP.LoadItem")
BENCH_STATIC(benchSprites,"GameAPP","GameAPP.LoadSprite")
BENCH_STATIC(benchMix,"MixData","MixData.InitMixData")
BENCH_STATIC(benchPlantData,"PlantDataManager","PlantDataManager.Init")
BENCH_STATIC(benchZombieData,"ZombieDataManager","ZombieDataManager.LoadData")
BENCH_STATIC(benchExplore,"ExploreDataManager","ExploreDataManager.LoadData")
static void (*benchAwakeOld)(P,M)=nullptr;
static void (*benchStartOld)(P,M)=nullptr;
#include "lazy_ui_candidate.inc"
static int benchCap=0;
static int benchReadCap(){FILE* f=fopen("/sdcard/Android/data/com.LanPiaoPiao.PlantsVsZombiesEN/files/bench-cap.txt","r");int cap=0;if(f){fscanf(f,"%d",&cap);fclose(f);}return cap;}
static void benchSetCap(int requested){if(requested!=30&&requested!=60&&requested!=120&&requested!=0)return;int cap=requested?requested:200;P args[]={&cap};call(method(cls("UnityEngine","Application"),"set_targetFrameRate",1),nullptr,args);benchCap=requested;BLOG("CAP requested=%d applied=%d",requested,cap);}
static void benchAwake(P o,M m){benchLoading=true;auto b=BenchClock::now();BLOG("BEGIN GameAPP.Awake since_hooks_us=%lld",benchUs(benchInit));benchAwakeOld(o,m);BLOG("END GameAPP.Awake us=%lld",benchUs(b));benchLoading=false;benchSetCap(benchReadCap());}
static void benchStart(P o,M m){auto b=BenchClock::now();BLOG("BEGIN GameAPP.Start");benchStartOld(o,m);BLOG("END GameAPP.Start us=%lld",benchUs(b));}
static std::vector<long long> benchFrames;
static void benchTick(){
 static auto previous=BenchClock::now(),report=previous,poll=previous;auto now=BenchClock::now();auto gap=std::chrono::duration_cast<std::chrono::microseconds>(now-previous).count();previous=now;benchFrames.push_back(gap);
 if(now-poll>std::chrono::milliseconds(500)){int cap=benchReadCap();if(cap!=benchCap)benchSetCap(cap);lazyUIPoll();poll=now;}
 if(now-report<std::chrono::seconds(5))return;
 auto total=std::chrono::duration_cast<std::chrono::microseconds>(now-report).count();auto sorted=benchFrames;std::sort(sorted.begin(),sorted.end());auto at=[&](double q){return sorted[std::min(sorted.size()-1,(size_t)(sorted.size()*q))];};auto slow=std::count_if(sorted.begin(),sorted.end(),[](auto n){return n>50000;});
 BLOG("FRAMES cap=%d count=%zu elapsed_us=%lld p50_us=%lld p95_us=%lld p99_us=%lld max_us=%lld over50ms=%zu",benchCap,sorted.size(),total,at(.5),at(.95),at(.99),sorted.back(),(size_t)slow);benchFrames.clear();report=now;
}
static void initializeStartupBench(){
 benchInit=BenchClock::now();BLOG("HOOKS BEGIN");initializeLazyUI();
 hook(cls("","GameAPP"),"Awake",0,(P)benchAwake,(P*)&benchAwakeOld);hook(cls("","GameAPP"),"Start",0,(P)benchStart,(P*)&benchStartOld);
#define HOOK_STAGE(symbol,klass,name) hook(cls("",klass),name,0,(P)symbol,(P*)&symbol##Old)
 HOOK_STAGE(benchResources,"ResourcesManager",".ctor");HOOK_STAGE(benchPlants,"ResourcesManager","LoadPlant");HOOK_STAGE(benchNormalSkin,"ResourcesManager","LoadNormalSkin");HOOK_STAGE(benchSkin,"ResourcesManager","LoadSkin");HOOK_STAGE(benchBullets,"ResourcesManager","LoadBullet");HOOK_STAGE(benchGrid,"ResourcesManager","LoadGridItem");HOOK_STAGE(benchGameResources,"GameAPP","LoadResources");HOOK_STAGE(benchSounds,"SoundManager","LoadSound");HOOK_STAGE(benchMusic,"SoundManager","LoadMusic");HOOK_STAGE(benchParticles,"GameAPP","LoadParticle");HOOK_STAGE(benchItems,"GameAPP","LoadItem");HOOK_STAGE(benchMix,"MixData","InitMixData");HOOK_STAGE(benchPlantData,"PlantDataManager","Init");HOOK_STAGE(benchZombieData,"ZombieDataManager","LoadData");HOOK_STAGE(benchExplore,"ExploreDataManager","LoadData");
BLOG("HOOKS END");
}
