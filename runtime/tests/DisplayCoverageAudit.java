import java.lang.reflect.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import com.silvershadow.pvzf.PlantbrushTranslations;

/** Audit post-translation display candidates; remaining CJK is evidence, not an automatic replacement request. */
public class DisplayCoverageAudit {
    static String dec(String s){return new String(Base64.getDecoder().decode(s),StandardCharsets.UTF_8);}
    static String enc(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
    public static void main(String[] args)throws Exception {
        Class<?> c=Class.forName("com.silvershadow.pvzf.EnglishActivity");
        Field ef=c.getDeclaredField("exact"),rf=c.getDeclaredField("rules");ef.setAccessible(true);rf.setAccessible(true);
        Map exact=(Map)ef.get(null);List rules=(List)rf.get(null);
        Constructor<?> ctor=Class.forName(c.getName()+"$Rule").getDeclaredConstructor(String.class,String.class);ctor.setAccessible(true);
        for(String line:Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8)){
            String[] row=line.split("\t",-1);
            if(row[0].equals("E"))exact.put(dec(row[1]),dec(row[2]));
            if(row[0].equals("R"))rules.add(ctor.newInstance(dec(row[1]),dec(row[2])));
        }
        for(String[] p:PlantbrushTranslations.EXACT)exact.put(p[0],p[1]);
        for(String[] p:PlantbrushTranslations.RULES)rules.add(ctor.newInstance(p[0],p[1]));
        Method translate=c.getMethod("translate",String.class);List<String> remaining=new ArrayList<>();int total=0;
        for(String line:Files.readAllLines(Paths.get(args[1]),StandardCharsets.UTF_8)){
            String[] row=line.split("\t",2);String original=dec(row[1]);String result=(String)translate.invoke(null,original);if(result==null)result=original;total++;
            if(result.matches("(?s).*[\\u3400-\\u9fff].*"))remaining.add(row[0]+"\t"+enc(result));
        }
        Files.write(Paths.get(args[2]),remaining,StandardCharsets.UTF_8);
        System.out.println(total+" candidates checked; "+remaining.size()+" retain CJK for review (includes internal keys and diagnostics)");
    }
}
