#pragma once
#include <type_traits>

// IL2CPP has different write conventions for values and object references.
// Keep them separate so a local pointer's address cannot become a managed object.
namespace english {
using FieldSetter = void (*)(void*, void*, void*);
template<class T>
void writeValueField(FieldSetter setter, void* object, void* field, T value) {
    static_assert(!std::is_pointer_v<T> && !std::is_null_pointer_v<T>,
                  "Managed references require writeObjectField");
    setter(object, field, &value);
}
inline void writeObjectField(FieldSetter setter, void* object, void* field, void* value) {
    setter(object, field, value);
}
}
