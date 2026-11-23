#include "../vehicle_grounding.h"
#include <cassert>
#include <limits>
int main(){
    constexpr float step=0.02f,ground=-4.2625f;
    // Independent regression model: the old velocity is held over several
    // physics steps between rendered frames. A subpixel error grows off-screen.
    float stock=ground+0.00001f,fixed=stock;
    for(int frame=0;frame<20;++frame){
        stock+=(ground-stock)/step*(4*step);
        float y;assert(english::groundedVehicleY(fixed,(ground-fixed)/step,step,y));
        fixed=y; // zero vertical velocity for all intervening physics steps
    }
    assert(std::abs(stock-ground)>1000);assert(std::abs(fixed-ground)<0.00001f);
    // Multiple render Updates can see the same Transform while the Rigidbody
    // already holds earlier corrections. The pre6/pre7 implementation added
    // the rendered error repeatedly to that newer body position and diverged.
    float previousBody=ground+0.00001f,correctedBody=previousBody;
    constexpr float axisOffset=0.7625f;
    for(int physics=0;physics<18;++physics){
        float renderedOld=previousBody,renderedNew=correctedBody;
        for(int update=0;update<4;++update){
            float oldError=(ground+axisOffset)-(renderedOld+axisOffset);
            previousBody+=oldError;
            float velocity=((ground+axisOffset)-(renderedNew+axisOffset))/step;
            float y;assert(english::groundedVehicleY(renderedNew,velocity,step,y));
            correctedBody=y;
        }
    }
    assert(std::abs(previousBody-ground)>1000);
    assert(std::abs(correctedBody-ground)<0.00001f);
    // Moving roof target and varying Update/physics ratios. Every correction
    // must keep the animated-axis offset without accumulating an old error.
    for(int frame=0;frame<100;++frame){
        float root=correctedBody,target=ground-0.02f*frame;
        for(int update=0;update<1+frame%7;++update){
            float velocity=((target+axisOffset)-(root+axisOffset))/step;
            float y;assert(english::groundedVehicleY(root,velocity,step,y));
            correctedBody=y;
        }
        assert(std::abs(correctedBody-target)<0.00001f);
    }
    // Copying the animated axis ground target would lift the car.
    float y;assert(english::groundedVehicleY(-4.2625f,0,step,y));assert(y==-4.2625f);
    assert(english::groundedVehicleY(-10,100,step,y));assert(std::abs(y+8)<0.00001f);
    // Bad data must leave the stock path intact, not inject invalid physics.
    float inf=std::numeric_limits<float>::infinity();
    assert(!english::groundedVehicleY(inf,0,step,y));
    assert(!english::groundedVehicleY(0,inf,step,y));
    assert(!english::groundedVehicleY(0,0,0,y));
}
