// A display-only fallback for one missing native 4.1 modifier description.
// The boxed enum and native unknown-result guard prevent relabeling other IDs.
static P modifierUltiClass=nullptr;
static P (*oldModifierText)(P,P,M)=nullptr;
static P modifierText(P self,P buff,M m){
    P result=oldModifierText(self,buff,m);
    if(!buff||il2cpp_object_get_class(buff)!=modifierUltiClass)return result;
    if(*static_cast<int*>(il2cpp_object_unbox(buff))!=52)return result;
    if(!sameText(result,u"未知索引")&&!sameText(result,u"Unknown Modifier ID"))return result;
    // Blooms 4.1 ultimateBuffs[52]. No gameplay value or dictionary is changed.
    return str("Obsidian Formation:\nObsidian Jugger-nut: While on the lawn, all Obsidian plants take reduced final damage based on the number of different Obsidian plants present.");
}
static void initializeModifierDisplay(){
    P k=cls("","UltiBuff");
    if(!k||!fieldInfo(k,"堡垒1")||!overload(cls("","TravelMgr"),"GetText",{"System.Object"})){
        LOG("Modifier display fallback: unexpected schema; disabled");return;
    }
    modifierUltiClass=k;
    hook(cls("","TravelMgr"),"GetText",1,(P)modifierText,(P*)&oldModifierText);
}
