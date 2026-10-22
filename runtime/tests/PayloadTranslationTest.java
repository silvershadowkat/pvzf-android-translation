import java.lang.reflect.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Offline display census using the real Java translator and the built payload. */
public final class PayloadTranslationTest {
    static String dec(String s){return new String(Base64.getDecoder().decode(s),StandardCharsets.UTF_8);}
    static String enc(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
    public static void main(String[] args)throws Exception {
        Class<?> c=Class.forName("com.silvershadow.pvzf.EnglishActivity");
        Field ef=c.getDeclaredField("exact");ef.setAccessible(true);Map exact=(Map)ef.get(null);
        Field rf=c.getDeclaredField("rules");rf.setAccessible(true);List rules=(List)rf.get(null);
        Class<?> r=Class.forName("com.silvershadow.pvzf.EnglishActivity$Rule");
        Constructor<?> ctor=r.getDeclaredConstructor(String.class,String.class);ctor.setAccessible(true);
        Method translate=c.getMethod("translate",String.class);List<String> output=new ArrayList<>();int checks=0;
        for(String line:Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8)){
            String[] row=line.split("\t",-1);
            if(row[0].equals("E"))exact.put(dec(row[1]),dec(row[2]));
            else if(row[0].equals("R"))rules.add(ctor.newInstance(dec(row[1]),dec(row[2])));
            else if(row[0].equals("T"))output.add(enc((String)translate.invoke(null,dec(row[1]))));
            else if(row[0].equals("C")){
                String source=dec(row[1]),expected=dec(row[2]),actual=(String)translate.invoke(null,source);
                if(!expected.equals(actual))throw new AssertionError("Display fixture failed: "+source+" => "+actual);
                checks++;
            }
        }
        Files.write(Paths.get(args[1]),output,StandardCharsets.UTF_8);
        System.out.println("Payload display census: "+output.size()+" occurrences; "+checks+" screenshot/regression fixtures passed.");
    }
}
