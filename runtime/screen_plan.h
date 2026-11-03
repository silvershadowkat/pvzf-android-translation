#pragma once
#include <cstdint>
struct ScreenPlan {int width=0,height=0;};
// Preserve the game's authored 16:9 frame while filling the physical surface.
// Bound rendering to the current pixel budget, including narrow tablets.
inline ScreenPlan stretchPlan(int width,int height){
    if(width<320||height<240||width>16384||height>16384)return {};
    if(int64_t(width)*9>int64_t(height)*16)width=int(int64_t(height)*16/9);
    else height=int(int64_t(width)*9/16);
    return {width&~1,height&~1};
}
