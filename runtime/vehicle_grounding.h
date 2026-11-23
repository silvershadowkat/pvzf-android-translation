#pragma once
#include <algorithm>
#include <cmath>
namespace english {
// Convert the stock one-physics-step correction into a direct vertical move.
// The stock error is measured from the rendered axis. Apply it to the rendered
// root, preserving the axis offset. Rigidbody.position may already include a
// correction that its Transform has not reflected yet; adding the same error
// there again makes multiple Updates per physics step amplify it.
inline bool groundedVehicleY(float renderedRootY,float verticalVelocity,float fixedStep,float& targetY) {
    if(!std::isfinite(renderedRootY)||!std::isfinite(verticalVelocity)||
       !std::isfinite(fixedStep)||fixedStep<=0) return false;
    targetY=renderedRootY+verticalVelocity*std::max(fixedStep,0.0001f);
    return std::isfinite(targetY);
}
}
