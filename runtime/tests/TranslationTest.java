import java.lang.reflect.*;
import java.util.*;

/** Exercise the actual static translator without launching Android UI. */
public final class TranslationTest {
    static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception {
        Class<?> c=Class.forName("com.silvershadow.pvzf.EnglishActivity");
        Field ef=c.getDeclaredField("exact");ef.setAccessible(true);
        Map<String,String> exact=(Map<String,String>)ef.get(null);
        exact.put("木桩","Voodoo Dummy");exact.put("强化：力量","Upgrade: Power");
        Field rf=c.getDeclaredField("rules");rf.setAccessible(true);
        List rules=(List)rf.get(null);
        Class<?> rule=Class.forName("com.silvershadow.pvzf.EnglishActivity$Rule");
        Constructor<?> constructor=rule.getDeclaredConstructor(String.class,String.class);constructor.setAccessible(true);
        rules.add(constructor.newInstance("获得(.+)！","Gain {0}!"));
        Method translate=c.getDeclaredMethod("translate",String.class);
        check(translate.invoke(null,"木桩").equals("Voodoo Dummy"),"exact");
        check(translate.invoke(null,"  木桩  ").equals("  Voodoo Dummy  "),"whitespace");
        check(translate.invoke(null,"获得木桩！").equals("Gain Voodoo Dummy!"),"capture translation");
        check(translate.invoke(null,"Header\r\n强化：力量\r\n木桩\n").equals("Header\r\nUpgrade: Power\r\nVoodoo Dummy\n"),"mixed panel and line endings");
        check(translate.invoke(null,"未知文字").equals("未知文字"),"unknown preservation");
        check(translate.invoke(null,"prefix木桩suffix").equals("prefix木桩suffix"),"no substring replacement");
        check(translate.invoke(null,"player name").equals("player name"),"English unchanged");
        check(translate.invoke(null,"<color=red><b>木桩</b></color>").equals("<color=red><b>Voodoo Dummy</b></color>"),"nested rich text");
        check(translate.invoke(null,"<size=18>强化：力量</size>\n<color=red>未知文字</color>").equals("<size=18>Upgrade: Power</size>\n<color=red>未知文字</color>"),"styled panel preserves unknowns");
        check(translate.invoke(null,"prefix<color=red>木桩</color>suffix").equals("prefix<color=red>Voodoo Dummy</color>suffix"),"complete styled segment only");
        check(translate.invoke(null,"<unknown>木桩</unknown>").equals("<unknown>木桩</unknown>"),"unrecognized markup preserved");
        check(translate.invoke(null,new Object[]{null})==null,"null");
        Field levelsField=c.getDeclaredField("onlineLevels");levelsField.setAccessible(true);
        Map<String,String[]> levels=(Map<String,String[]>)levelsField.get(null);
        levels.put("level_1_test",new String[]{"PC Level","PC opening tip"});
        levels.put("level_2_test",new String[]{"Another Level","Different tip"});
        Method title=c.getMethod("onlineTitle",String.class,String.class);
        Method register=c.getMethod("registerOnlineLevel",String.class,String.class,String.class);
        check(title.invoke(null,"level_1_test","原始关卡").equals("PC Level"),"ID-based title");
        check(title.invoke(null,"unknown","原始关卡").equals("原始关卡"),"unknown level unchanged");
        register.invoke(null,"level_1_test","原始关卡","开场提示");
        check(translate.invoke(null,"开场提示").equals("PC opening tip"),"opening tip display registration");
        register.invoke(null,"level_2_test","其他关卡","开场提示");
        check(translate.invoke(null,"开场提示").equals("开场提示"),"ambiguous tips fail closed");
        check(translate.invoke(null,"原始关卡").equals("PC Level"),"separate level title retained");
        System.out.println("Display translation behavior checks passed: 17");
    }
}
