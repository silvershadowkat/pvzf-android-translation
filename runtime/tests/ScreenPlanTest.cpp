#include "../screen_plan.h"
#include <cassert>
#include <cmath>
int main(){
    // Ultra-wide phone, 7:5 tablet, 4:3 handheld, 16:9 panel and low resolution.
    ScreenPlan inputs[]={{3120,1440},{2800,2000},{1440,1080},{1920,1080},{854,480}};
    for(auto input:inputs){
        auto p=stretchPlan(input.width,input.height);
        assert(p.width>0&&p.height>0&&p.width<=input.width&&p.height<=input.height);
        assert((p.width%2)==0&&(p.height%2)==0);
        assert(std::abs(double(p.width)/p.height-16.0/9)<0.01);
        // The captured default remains a separate exact value, not a transformed
        // previous request that accumulates changes on repeated toggles.
        assert(input.width>=p.width&&input.height>=p.height);
    }
    assert(stretchPlan(0,0).width==0);
    assert(stretchPlan(20000,1080).width==0);
    assert(stretchPlan(-1,1080).width==0);
}
