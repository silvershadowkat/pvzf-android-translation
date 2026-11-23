// In stock Android 4.1, grounded driver movement runs from Zombie.Update.
// SetGroundedDriverVelocity divides its ground-height error by fixedDeltaTime.
// Multiple physics steps before the next Update repeatedly integrate that same
// correction, amplifying tiny vertical errors until the vehicle leaves the lawn.
#include "vehicle_grounding.h"
static void (*oldGroundedVehicleVelocity)(P,float,M)=nullptr;
static M vehicleGetVelocity=nullptr,vehicleGetPosition=nullptr;
static M vehicleSetVelocity=nullptr,vehicleSetPosition=nullptr,vehicleFixedStep=nullptr;
static M vehicleGetTransform=nullptr,vehicleGetWorldPosition=nullptr;
static void groundedVehicleVelocity(P zombie,float vx,M m){
    oldGroundedVehicleVelocity(zombie,vx,m);
    // Preserve the game's target ground height, roof offset and horizontal speed.
    // Its caller still owns slowing, direction, attack, death and ice-road logic.
    P rb=field<P>(zombie,"rb");if(!rb)return;
    P boxedVelocity=call(vehicleGetVelocity,rb),boxedPosition=call(vehicleGetPosition,rb);
    P boxedStep=call(vehicleFixedStep);
    P transform=call(vehicleGetTransform,zombie);
    P boxedRoot=transform?call(vehicleGetWorldPosition,transform):nullptr;
    if(!boxedVelocity||!boxedPosition||!boxedStep||!boxedRoot)return;
    V2 velocity=value<V2>(boxedVelocity),position=value<V2>(boxedPosition);float y;
    if(!std::isfinite(velocity.x)||!english::groundedVehicleY(value<V3>(boxedRoot).y,velocity.y,value<float>(boxedStep),y))return;
    position.y=y;velocity.y=0;
    P positionArgs[]={&position},velocityArgs[]={&velocity};
    call(vehicleSetPosition,rb,positionArgs);
    call(vehicleSetVelocity,rb,velocityArgs);
}
static void initializeVehicleGrounding(){
    P rb=cls("UnityEngine","Rigidbody2D");
    vehicleGetVelocity=overload(rb,"get_velocity",{});
    vehicleGetPosition=overload(rb,"get_position",{});
    vehicleSetVelocity=overload(rb,"set_velocity",{"UnityEngine.Vector2"});
    vehicleSetPosition=overload(rb,"set_position",{"UnityEngine.Vector2"});
    vehicleFixedStep=overload(cls("UnityEngine","Time"),"get_fixedDeltaTime",{});
    vehicleGetTransform=overload(cls("UnityEngine","Component"),"get_transform",{});
    vehicleGetWorldPosition=overload(cls("UnityEngine","Transform"),"get_position",{});
    P driver=cls("","DriverZombie");
    if(!fieldInfo(driver,"rb")||!vehicleGetVelocity||!vehicleGetPosition||
       !vehicleSetVelocity||!vehicleSetPosition||!vehicleFixedStep||
       !vehicleGetTransform||!vehicleGetWorldPosition||
       !overload(driver,"SetGroundedDriverVelocity",{"System.Single"})){
        LOG("Vehicle grounding repair: unexpected schema; disabled");return;
    }
    if(hook(driver,"SetGroundedDriverVelocity",1,(P)groundedVehicleVelocity,(P*)&oldGroundedVehicleVelocity))
        LOG("Grounded vehicle vertical correction stabilized");
}
