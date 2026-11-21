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
    // The animated axis is offset from the physics origin. Keep the physics
    // origin's correction; copying the axis ground target would lift the car.
    float y;assert(english::groundedVehicleY(-4.2625f,0,step,y));assert(y==-4.2625f);
    assert(english::groundedVehicleY(-10,100,step,y));assert(std::abs(y+8)<0.00001f);
    // Bad data must leave the stock path intact, not inject invalid physics.
    float inf=std::numeric_limits<float>::infinity();
    assert(!english::groundedVehicleY(inf,0,step,y));
    assert(!english::groundedVehicleY(0,inf,step,y));
    assert(!english::groundedVehicleY(0,0,0,y));
}
