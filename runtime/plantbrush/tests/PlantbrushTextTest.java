import java.lang.reflect.*;
import java.util.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import com.silvershadow.pvzf.PlantbrushTranslations;
public class PlantbrushTextTest {
 public static void main(String[] args)throws Exception {
  Class<?> c=Class.forName("com.silvershadow.pvzf.EnglishActivity");Field e=c.getDeclaredField("exact"),r=c.getDeclaredField("rules");e.setAccessible(true);r.setAccessible(true);
  Map exact=(Map)e.get(null);List rules=(List)r.get(null);Constructor<?> ctor=Class.forName("com.silvershadow.pvzf.EnglishActivity$Rule").getDeclaredConstructor(String.class,String.class);ctor.setAccessible(true);
  List<String[]> census=new ArrayList<>();
  for(String file:args)for(String line:Files.readAllLines(Paths.get(file),StandardCharsets.UTF_8)) {
   String[] row=line.split("\t",-1);
   for(int i=1;i<row.length;i++)row[i]=new String(Base64.getDecoder().decode(row[i]),StandardCharsets.UTF_8);
   if(row[0].equals("E"))exact.put(row[1],row[2]);
   else if(row[0].equals("R"))rules.add(ctor.newInstance(row[1],row[2]));
   else census.add(row);
  }
  for(String[] x:PlantbrushTranslations.EXACT)exact.put(x[0],x[1]);for(String[] x:PlantbrushTranslations.RULES)rules.add(ctor.newInstance(x[0],x[1]));
  Method t=c.getMethod("translate",String.class);
  String[][] tests={{"铅笔  /  笔宽 6  /  256 × 256","Pencil / Width 6 / 256 × 256"},{"相似度：78.5 %\n强度：2.48\n选择这株植物","Similarity: 78.5 %\nStrength: 2.48\nChoose this plant"},{"[神笔马良] 鉴定失败：Draw a plant.","[Magic Plantbrush] Draw a plant."},{"获得植物：Sturdy-shroom\n强度 = 2.48\n相似度 = 0.78475","Plant received: Sturdy-shroom\nStrength = 2.48\nSimilarity = 0.78475"},{"未知植物名","未知植物名"}};
  String error="[Magic Plantbrush] 本地识别服务未就绪或请求失败：Received no data in response.。请启动神笔马良本地服务。\n<color=red>请确认是否启动了最新版神笔马良识图AI，可前往融合wiki下载</color>";
  String want="[Magic Plantbrush] Recognition service unavailable: Received no data in response.\nRestart the game and try again.";
  if(!want.equals(t.invoke(null,error)))throw new AssertionError("Service failure text: "+t.invoke(null,error));
  for(String[] x:tests)if(!x[1].equals(t.invoke(null,x[0])))throw new AssertionError(x[0]);
  int checks=6;
  for(String[] x:PlantbrushTranslations.REQUEST_ERRORS)for(String prefix:new String[]{"","[神笔马良] 鉴定失败：","[Magic Plantbrush] ","[Magic Plantbrush] 鉴定失败："})for(String suffix:new String[]{"","\n<color=red>请确认是否启动了最新版神笔马良识图AI，可前往融合wiki下载</color>"}) {
   String source=prefix+x[0]+suffix,actual=(String)t.invoke(null,source);
   if(actual.matches("(?s).*[\\u3400-\\u9fff].*"))throw new AssertionError("Composed error remains Chinese: "+actual);
   if(!actual.contains(x[1]))throw new AssertionError("Wrong error: "+actual);
   checks++;
  }
  for(String[] row:census){
   String actual=(String)t.invoke(null,row[1]);
   if(row[0].equals("C")&&!actual.equals(row[2]))throw new AssertionError(row[1]+" => "+actual+" != "+row[2]);
   if(row[0].equals("T")&&actual.matches("(?s).*[\\u3400-\\u9fff].*"))throw new AssertionError("Audit gap: "+row[1]+" => "+actual);
   checks++;
  }
  System.out.println("Shared drawing text: "+checks+" actual-translator fixtures passed");
 }
}
