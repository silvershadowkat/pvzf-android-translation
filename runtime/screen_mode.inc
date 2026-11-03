#include "screen_plan.h"
static uint32_t screenButton=0;
static bool screenFilled=false,screenPending=false,screenWanted=false;
static ScreenPlan screenOriginal,screenRequested;
static bool screenOriginalFull=true;
static std::chrono::steady_clock::time_point screenDeadline;
static void refreshScreen(){
    P b=target(screenButton);
    if(alive(b))label(b,screenPending?"Screen: Applying":screenFilled?"Screen: Stretch":"Screen: Default");
}
static void toggleScreen(){
    if(screenPending)return;
    P c=cls("UnityEngine","Screen");
    M resize=overload(c,"SetResolution",{"System.Int32","System.Int32","System.Boolean"});
    if(!resize)return;
    int width=value<int>(call(method(c,"get_width",0)));
    int height=value<int>(call(method(c,"get_height",0)));
    if(!screenFilled){
        screenOriginal={width,height};screenOriginalFull=value<bool>(call(method(c,"get_fullScreen",0)));
        screenRequested=stretchPlan(width,height);
    }else screenRequested=screenOriginal;
    if(!screenRequested.width||!screenRequested.height)return;
    bool full=screenFilled?screenOriginalFull:true;
    P args[]={&screenRequested.width,&screenRequested.height,&full};
    call(resize,nullptr,args);
    screenWanted=!screenFilled;screenPending=true;
    screenDeadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    refreshScreen();
}
static void screenTick(){
    if(!screenPending)return;
    P c=cls("UnityEngine","Screen");
    int width=value<int>(call(method(c,"get_width",0)));
    int height=value<int>(call(method(c,"get_height",0)));
    if(std::abs(width-screenRequested.width)<=2&&std::abs(height-screenRequested.height)<=2){
        screenFilled=screenWanted;screenPending=false;refreshScreen();
        LOG("Screen mode %s applied: %dx%d; captured default %dx%d",screenFilled?"Stretch":"Default",width,height,screenOriginal.width,screenOriginal.height);
    }else if(std::chrono::steady_clock::now()>screenDeadline){
        LOG("Requested display dimensions not accepted: %dx%d -> %dx%d",screenRequested.width,screenRequested.height,width,height);
        // Restore the captured default, never guess a fixed resolution. A later
        // explicit button press can retry. No startup or recurring resize runs.
        M resize=overload(c,"SetResolution",{"System.Int32","System.Int32","System.Boolean"});
        P args[]={&screenOriginal.width,&screenOriginal.height,&screenOriginalFull};call(resize,nullptr,args);
        screenPending=false;screenFilled=false;refreshScreen();
    }
}
