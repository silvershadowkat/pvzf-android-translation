#pragma once
#include <algorithm>
#include <cmath>
namespace english {
// Convert the stock one-physics-step correction into a direct vertical move.
// Use the Rigidbody origin, not the animated axis (which has a prefab offset).
inline bool groundedVehicleY(float bodyY,float verticalVelocity,float fixedStep,float& targetY) {
    if(!std::isfinite(bodyY)||!std::isfinite(verticalVelocity)||
       !std::isfinite(fixedStep)||fixedStep<=0) return false;
    targetY=bodyY+verticalVelocity*std::max(fixedStep,0.0001f);
    return std::isfinite(targetY);
}
}
