// Experimental 4.1 startup probe. Included only by build_startup_probe.py, never normal runtime builds.
#include <unordered_set>
struct LazyUIResource {int kind;const char* path;const char* name;};
static const LazyUIResource lazyUIResources[]={
{0,"ui/prefabs/mainmenu","MainMenu"},
{1,"ui/prefabs/mainmenu_travel","MainMenu_travel"},
{2,"ui/prefabs/losemenu","LoseMenu"},
{3,"ui/prefabs/othermenu","OtherMenu"},
{4,"ui/prefabs/optionmenu","OptionMenu"},
{5,"ui/prefabs/noticepausemenu","NoticePauseMenu"},
{6,"ui/prefabs/challengemenu","ChallengeMenu"},
{7,"ui/prefabs/izmenu","IZMenu"},
{8,"ui/prefabs/izbottommenu","IZBottomMenu"},
{9,"ui/prefabs/survivalmenu","SurvivalMenu"},
{10,"ui/prefabs/exploremenu","ExploreMenu"},
{11,"ui/prefabs/exploremakemenu","ExploreMakeMenu"},
{12,"ui/prefabs/traveladvanturemenu","TravelAdvantureMenu"},
{13,"ui/prefabs/travelgamemenu","TravelGameMenu"},
{14,"ui/prefabs/travelchallengemenu","TravelChallengeMenu"},
{15,"ui/prefabs/travelmenu","TravelMenu"},
{16,"ui/prefabs/pausemenu","PauseMenu"},
{17,"ui/prefabs/pausemenu_checkquit","PauseMenu_checkQuit"},
{18,"ui/prefabs/pausemenu_checkrestart","PauseMenu_checkRestart"},
{19,"ui/prefabs/gardenstoremenu","GardenStoreMenu"},
{20,"ui/prefabs/gardenui","GardenUI"},
{21,"ui/prefabs/zumaui","ZumaUI"},
{22,"ui/prefabs/ingameui","InGameUI"},
{23,"ui/prefabs/ingameui_iz","InGameUI_IZ"},
{24,"ui/prefabs/warningmenu_travel","WarningMenu_travel"},
{25,"ui/prefabs/travelstore","TravelStore"},
{26,"ui/prefabs/travelbuffmenu","TravelBuffMenu"},
{27,"ui/prefabs/travellookmenu","TravelLookMenu"},
{28,"ui/prefabs/travelinvestmenu","TravelInvestMenu"},
{29,"ui/prefabs/travelsynergymenu","TravelSynergyMenu"},
{30,"ui/prefabs/levelsavemenu","LevelSaveMenu"},
{31,"ui/prefabs/sellconfirm","SellConfirm"},
{32,"ui/prefabs/buyconfirm","BuyConfirm"},
{37,"ui/prefabs/jigsawhelpmenu","JigsawHelpMenu"},
{38,"ui/prefabs/fruitninjamenu","FruitNinjaMenu"},
{39,"ui/prefabs/playershootingmenu","PlayerShootingMenu"},
{40,"ui/prefabs/gardenworldui","GardenWorldUI"},
{41,"ui/prefabs/gardenprotectionmenu","GardenProtectionMenu"},
{42,"ui/prefabs/towermenu","TowerMenu"},
{43,"ui/prefabs/towerupgrademenu","TowerUpgradeMenu"},
{44,"ui/prefabs/treasuremainmenu","TreasureMainMenu"},
{45,"ui/prefabs/treasurewarehousemenu","TreasureWarehouseMenu"},
{46,"ui/prefabs/treasurestoremenu","TreasureStoreMenu"},
{47,"ui/prefabs/treasureconfirmmenu","TreasureConfirmMenu"},
{48,"ui/prefabs/treasuresettlemenu","TreasureSettleMenu"},
{49,"ui/prefabs/treasureequipmentmenu","TreasureEquipmentMenu"},
{50,"ui/prefabs/treasureupgrademenu","TreasureUpgradeMenu"},
{51,"ui/prefabs/treasureevacuatemenu","TreasureEvacuateMenu"},
{52,"ui/prefabs/biggardenui","BigGardenUI"},
{53,"ui/prefabs/gardenbagmenu","GardenBagMenu"},
{54,"ui/prefabs/plantinfomenu","PlantInfoMenu"},
{55,"ui/prefabs/almanacmenu","AlmanacMenu"},
{56,"ui/prefabs/almanacplantmenu","AlmanacPlantMenu"},
{57,"ui/prefabs/almanaczombiemenu","AlmanacZombieMenu"},
{58,"ui/prefabs/evebuffmenu","EveBuffMenu"},
{59,"ui/prefabs/plantdamagemenu","PlantDamageMenu"},
{60,"ui/prefabs/advanturemenu","AdvantureMenu"},
{61,"ui/prefabs/advanturemenu2","AdvantureMenu2"},
{62,"ui/prefabs/advanturemissionmenu","AdvantureMissionMenu"},
{63,"ui/prefabs/advanturestarmenu","AdvantureStarMenu"},
{64,"ui/prefabs/advanturehelpmenu","AdvantureHelpMenu"},
{65,"ui/prefabs/advantureevolutionmenu","AdvantureEvolutionMenu"},
{66,"ui/prefabs/godshootingmenu","GodShootingMenu"},
{67,"ui/prefabs/godshootingplantmenu","GodShootingPlantMenu"},
{68,"ui/prefabs/confirmmenu","ConfirmMenu"},
{69,"ui/prefabs/plantdatamenu","PlantDataMenu"},
{70,"ui/prefabs/custommenu","CustomMenu"},
{71,"ui/prefabs/customlevelmenu","CustomLevelMenu"},
{72,"ui/prefabs/customonlinemenu","CustomOnlineMenu"},
{73,"ui/prefabs/inputkeymenu","InputKeyMenu"},
{74,"ui/prefabs/playersavemenu","PlayerSaveMenu"},
{75,"ui/prefabs/renamemenu","ReNameMenu"},
{76,"ui/prefabs/levelresultmenu","LevelResultMenu"},
{77,"ui/prefabs/pausemenu_mainmenu","PauseMenu_mainMenu"},
{78,"ui/prefabs/rhythmgamecharteditorui","RhythmGameChartEditorUI"},
{79,"ui/prefabs/almanacselectmenu","AlmanacSelectMenu"},
{80,"ui/prefabs/multiplechoicemenu","MultipleChoiceMenu"},
{81,"ui/prefabs/multiplechoicemenu2","MultipleChoiceMenu2"},
{82,"ui/prefabs/almanacbuffmenu","AlmanacBuffMenu"},
{83,"ui/prefabs/pumpinerchestmenu","PumpinerChestMenu"},
{84,"ui/prefabs/hotlevelmenu","HotLevelMenu"},
{85,"ui/prefabs/uiconfigmenu","UIConfigMenu"},
{86,"ui/prefabs/abyssmenu","AbyssMenu"},
{87,"ui/prefabs/abyssstoragemenu","AbyssStorageMenu"},
{88,"ui/prefabs/abysslotterymenu","AbyssLotteryMenu"},
{89,"ui/prefabs/abysslotteryanimmenu","AbyssLotteryAnimMenu"},
{90,"ui/prefabs/openblivemenu","OpenBLiveMenu"},
{91,"ui/prefabs/scratchoffmenu","ScratchOffMenu"},
{92,"ui/prefabs/almanacshootingmenu","AlmanacShootingMenu"},
{93,"ui/prefabs/nightsnowadvanturemenu","NightSnowAdvantureMenu"},
{94,"ui/prefabs/maliangmenu","MaLiangMenu"},
{95,"ui/prefabs/multiplechoicemenu3","MultipleChoiceMenu3"},
{96,"ui/prefabs/hovergardeninterface","HoverGardenInterface"},
{97,"ui/prefabs/hovergardenpanel","HoverGardenPanel"},
};
static std::unordered_set<P> lazyUIOwners;
static P (*lazyFieldType)(P)=nullptr;
static P (*lazyClassFromType)(P)=nullptr;
static void (*lazyUICtorOld)(P,M)=nullptr;
static P (*lazyPushOld)(P,int,P,bool,M)=nullptr;
static int lazyUIReadMode(){FILE* f=fopen("/sdcard/Android/data/com.LanPiaoPiao.PlantsVsZombiesEN/files/bench-ui.txt","r");int mode=0;if(f){fscanf(f,"%d",&mode);fclose(f);}return mode;}
static P lazyNewField(P owner,const char* name){
 P field=fieldInfo(il2cpp_object_get_class(owner),name);if(!field||!lazyFieldType||!lazyClassFromType)return nullptr;
 P c=lazyClassFromType(lazyFieldType(field));if(!c)return nullptr;
 M ctor=method(c,".ctor",0);if(!ctor||!*(P*)ctor)return nullptr;
 P o=il2cpp_object_new(c);if(!o)return nullptr;P exception=nullptr;il2cpp_runtime_invoke(ctor,o,nullptr,&exception);return exception?nullptr:o;
}
static void lazyUICtor(P o,M m){
 auto begin=BenchClock::now();int mode=lazyUIReadMode();BLOG("BEGIN UIResourcesLoader.ctor mode=%d",mode);
 if(mode==1){
  P dict=lazyNewField(o,"UIPrefabs"),stack=lazyNewField(o,"menuStack");
  if(dict&&stack){setreffield(o,"UIPrefabs",dict);setreffield(o,"menuStack",stack);lazyUIOwners.insert(o);}
  else{BLOG("LAZYUI initialization unavailable; falling back");lazyUICtorOld(o,m);}
 }else lazyUICtorOld(o,m);
 BLOG("END UIResourcesLoader.ctor us=%lld mode=%d count=%d",benchUs(begin),mode,value<int>(call(field<P>(o,"UIPrefabs"),"get_Count")));
}
static bool lazyUIEnsure(P loader,int kind){
 if(!lazyUIOwners.count(loader))return true;
 P dict=field<P>(loader,"UIPrefabs");if(!dict)return false;
 P key[]={&kind};if(value<bool>(call(dict,"ContainsKey",1,key)))return true;
 const LazyUIResource* found=nullptr;for(const auto& row:lazyUIResources)if(row.kind==kind){found=&row;break;}
 if(!found){BLOG("LAZYUI unknown kind=%d; preserving original missing-key behavior",kind);return false;}
 auto begin=BenchClock::now();P args[]={str(found->path),type(cls("UnityEngine","GameObject"))};P prefab=call(overload(cls("UnityEngine","Resources"),"Load",{"System.String","System.Type"}),nullptr,args);
 if(!alive(prefab)||name(prefab)!=found->name){BLOG("LAZYUI resource unavailable kind=%d path=%s",kind,found->path);return false;}
 P set[]={&kind,prefab};call(dict,"set_Item",2,set);BLOG("LAZYUI loaded kind=%d path=%s us=%lld",kind,found->path,benchUs(begin));return value<bool>(call(dict,"ContainsKey",1,key));
}
static P lazyPush(P loader,int kind,P transform,bool group,M m){lazyUIEnsure(loader,kind);return lazyPushOld(loader,kind,transform,group,m);}
static void lazyUIValidate(){
 P loader=stat("GameAPP","UIManager");unsigned ok=0;for(const auto& row:lazyUIResources)if(lazyUIEnsure(loader,row.kind))++ok;
 BLOG("LAZYUI validation resources=%zu ok=%u dictionary=%d",sizeof(lazyUIResources)/sizeof(lazyUIResources[0]),ok,value<int>(call(field<P>(loader,"UIPrefabs"),"get_Count")));
}
static void lazyUIPoll(){
 const char* file="/sdcard/Android/data/com.LanPiaoPiao.PlantsVsZombiesEN/files/bench-ui-command.txt";FILE* f=fopen(file,"r");if(!f)return;int command=-1;fscanf(f,"%d",&command);fclose(f);remove(file);
 if(command==-2){lazyUIValidate();return;}
 if(command==-3){call(stat("GameAPP","UIManager"),"Pop");BLOG("LAZYUI popped menu");return;}
 if(command<0)return;
 P loader=stat("GameAPP","UIManager"),canvas=stat("GameAPP","canvasUp");bool group=false;P args[]={&command,canvas,&group};P menu=call(overload(cls("","UIResourcesLoader"),"Push",{"UIType","UnityEngine.Transform","System.Boolean"}),loader,args);BLOG("LAZYUI pushed kind=%d result=%s",command,menu?"ok":"null");
}
static void initializeLazyUI(){
 P lib=dlopen("libil2cpp.so",RTLD_NOW|RTLD_NOLOAD);lazyFieldType=lib?reinterpret_cast<decltype(lazyFieldType)>(dlsym(lib,"il2cpp_field_get_type")):nullptr;lazyClassFromType=lib?reinterpret_cast<decltype(lazyClassFromType)>(dlsym(lib,"il2cpp_class_from_type")):nullptr;
 if(!lazyFieldType||!lazyClassFromType){BLOG("LAZYUI metadata API unavailable");return;}
 hook(cls("","UIResourcesLoader"),".ctor",0,(P)lazyUICtor,(P*)&lazyUICtorOld);hook(cls("","UIResourcesLoader"),"Push",3,(P)lazyPush,(P*)&lazyPushOld);
}
