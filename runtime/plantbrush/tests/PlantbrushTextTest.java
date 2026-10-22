import java.lang.reflect.*;
import java.util.*;
import com.silvershadow.pvzf.PlantbrushTranslations;
public class PlantbrushTextTest {
 public static void main(String[] args)throws Exception {
  Class<?> c=Class.forName("com.silvershadow.pvzf.EnglishActivity");Field e=c.getDeclaredField("exact"),r=c.getDeclaredField("rules");e.setAccessible(true);r.setAccessible(true);
  Map exact=(Map)e.get(null);List rules=(List)r.get(null);Constructor<?> ctor=Class.forName("com.silvershadow.pvzf.EnglishActivity$Rule").getDeclaredConstructor(String.class,String.class);ctor.setAccessible(true);
  for(String[] x:PlantbrushTranslations.EXACT)exact.put(x[0],x[1]);for(String[] x:PlantbrushTranslations.RULES)rules.add(ctor.newInstance(x[0],x[1]));
  Method t=c.getMethod("translate",String.class);
  String[][] tests={{"铅笔  /  笔宽 6  /  256 × 256","Pencil / Width 6 / 256 × 256"},{"相似度：78.5 %\n强度：2.48\n选择这株植物","Similarity: 78.5 %\nStrength: 2.48\nChoose this plant"},{"[神笔马良] 鉴定失败：Draw a plant.","[Magic Plantbrush] Draw a plant."},{"获得植物：Sturdy-shroom\n强度 = 2.48\n相似度 = 0.78475","Plant received: Sturdy-shroom\nStrength = 2.48\nSimilarity = 0.78475"},{"未知植物名","未知植物名"}};
  for(String[] x:tests)if(!x[1].equals(t.invoke(null,x[0])))throw new AssertionError(x[0]);
  System.out.println("Shared drawing text: 5 actual-translator fixtures passed");
 }
}
