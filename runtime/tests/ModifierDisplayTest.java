import java.nio.file.*;
import java.nio.charset.StandardCharsets;
/** Check original and partially translated card descriptions through the real translator. */
public final class ModifierDisplayTest {
 public static void main(String[] args)throws Exception {
  TranslationParityTest.Engine engine=new TranslationParityTest.Engine("com.silvershadow.pvzf.EnglishActivity");
  java.util.List<String> lines=Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8);
  for(String line:lines){String[] row=line.split("\t",-1);
   if(row[0].equals("E"))engine.exact.put(TranslationParityTest.dec(row[1]),TranslationParityTest.dec(row[2]));
   if(row[0].equals("R"))engine.rules.add(engine.ctor.newInstance(TranslationParityTest.dec(row[1]),TranslationParityTest.dec(row[2])));
  }
  int cases=0;
  for(String line:lines){String[] row=line.split("\t",-1);if(!row[0].equals("M"))continue;
   String expected=TranslationParityTest.dec(row[3]);
   for(int i=1;i<=2;i++)if(!expected.equals(engine.apply(TranslationParityTest.dec(row[i]))))throw new AssertionError("Incomplete modifier: "+expected);
   cases++;
  }
  if(cases!=3)throw new AssertionError("Missing card fixtures");
  System.out.println("Three modifier cards fully translated from original and mixed-language variants");
 }
}
