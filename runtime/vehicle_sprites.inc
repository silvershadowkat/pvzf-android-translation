// Android 4.1 LoadSprite assigns the heavily damaged rear sprite to both
// rear-body damage stages. Repair only that exact, confirmed cache state.
static void (*oldLoadVehicleSprites)(M)=nullptr;
static void (*vehicleWriteBarrier)(P,P*,P)=nullptr;
static void loadVehicleSprites(M m){
    oldLoadVehicleSprites(m);
    P cache=stat("GameAPP","spritePrefab");
    if(!cache||il2cpp_array_length(cache)<33||!vehicleWriteBarrier)return;
    P* items=reinterpret_cast<P*>(static_cast<char*>(cache)+sizeof(P)*4);
    if(!items[29]||!items[30]||!items[31]||items[31]!=items[32])return;
    if(name(items[29])!="Zombie_zamboni_1_damage1"||
       name(items[30])!="Zombie_zamboni_1_damage2"||
       name(items[31])!="Zombie_zamboni_2_damage2")return;
    P args[]={str("Zombies/Zombie_Driver/Zombie_zamboni_2_damage1"),type(cls("UnityEngine","Sprite"))};
    P replacement=call(overload(cls("UnityEngine","Resources"),"Load",{"System.String","System.Type"}),nullptr,args);
    if(!alive(replacement)||name(replacement)!="Zombie_zamboni_2_damage1"){
        LOG("Zomboni rear damage sprite unavailable; original cache retained");return;
    }
    // Managed array references require the IL2CPP GC write barrier.
    vehicleWriteBarrier(cache,&items[31],replacement);
    LOG("Zomboni rear damage stages restored: damage1 / damage2");
}
static void initializeVehicleSprites(){
    P lib=dlopen("libil2cpp.so",RTLD_NOW|RTLD_NOLOAD);
    vehicleWriteBarrier=lib?reinterpret_cast<decltype(vehicleWriteBarrier)>(dlsym(lib,"il2cpp_gc_wbarrier_set_field")):nullptr;
    if(!vehicleWriteBarrier||!fieldInfo(cls("","GameAPP"),"spritePrefab")||
       !overload(cls("UnityEngine","Resources"),"Load",{"System.String","System.Type"})){
        LOG("Vehicle sprite repair: unexpected schema; disabled");return;
    }
    hook(cls("","GameAPP"),"LoadSprite",0,(P)loadVehicleSprites,(P*)&oldLoadVehicleSprites);
}
