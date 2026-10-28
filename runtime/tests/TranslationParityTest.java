import java.lang.reflect.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;
import com.silvershadow.pvzf.RegexPrefix;
import com.silvershadow.pvzf.PlantbrushTranslations;

/** Compare optimized translation output with a frozen released translator. */
public final class TranslationParityTest {
    static String dec(String x){return new String(Base64.getDecoder().decode(x),StandardCharsets.UTF_8);}
    static final class Engine {
        final Class<?> c;final Map exact;final List rules;final Constructor<?> ctor;final Method translate;
        Engine(String name)throws Exception {
            c=Class.forName(name);Field e=c.getDeclaredField("exact"),r=c.getDeclaredField("rules");e.setAccessible(true);r.setAccessible(true);exact=(Map)e.get(null);rules=(List)r.get(null);
            ctor=Class.forName(name+"$Rule").getDeclaredConstructor(String.class,String.class);ctor.setAccessible(true);translate=c.getMethod("translate",String.class);
        }
        String apply(String x)throws Exception{return (String)translate.invoke(null,x);}
    }
    public static void main(String[] args)throws Exception {
        Engine old=new Engine("com.silvershadow.pvzf.BaselineEnglishActivity"),now=new Engine("com.silvershadow.pvzf.EnglishActivity");
        LinkedHashSet<String> tests=new LinkedHashSet<>();List<String> patterns=new ArrayList<>();int styled=0;
        for(String line:Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8)) {
            String[] row=line.split("\t",-1);String a=dec(row[1]);
            if(row[0].equals("E")){
                String b=dec(row[2]);old.exact.put(a,b);now.exact.put(a,b);tests.add(a);
                if(styled++<300){tests.add("<color=red>"+a+"</color>");tests.add(" "+a+" ");}
            } else if(row[0].equals("R")){
                String b=dec(row[2]);old.rules.add(old.ctor.newInstance(a,b));now.rules.add(now.ctor.newInstance(a,b));patterns.add(a);
            } else if(row[0].equals("C")||row[0].equals("T"))tests.add(a);
        }
        for(String[] x:PlantbrushTranslations.EXACT){old.exact.put(x[0],x[1]);now.exact.put(x[0],x[1]);tests.add(x[0]);}
        for(String[] x:PlantbrushTranslations.RULES){old.rules.add(old.ctor.newInstance(x[0],x[1]));now.rules.add(now.ctor.newInstance(x[0],x[1]));patterns.add(x[0]);}
        for(int i=0;i<200;i++){tests.add("未知性能测试 "+i);tests.add("铅笔  /  笔宽 "+i+"  /  256 × 256");}
        for(String x:tests)if(!Objects.equals(old.apply(x),now.apply(x)))throw new AssertionError("Translation changed: "+x);
        long total=0,rejected=0;
        for(String p:patterns){Pattern pattern=Pattern.compile(p);String prefix=RegexPrefix.of(p);
            int n=0;for(String x:tests){if(n++>=250)break;boolean skip=!x.startsWith(prefix);total++;if(skip){rejected++;if(pattern.matcher(x).matches())throw new AssertionError("Prefix rejects a valid match: "+p);}}
        }
        System.out.println("Released/optimized translator parity: "+tests.size()+" strings; exact entries, styled/padded text, census and changing-number messages unchanged.");
        System.out.println("Conservative prefix checks avoided "+rejected+" of "+total+" potential matcher creations on sampled text; this is not a device FPS benchmark.");
    }
}
