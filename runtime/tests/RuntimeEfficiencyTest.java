import com.silvershadow.pvzf.MusicStamp;
import com.silvershadow.pvzf.BoundedTextCache;
import com.silvershadow.pvzf.RegexPrefix;
import java.nio.file.*;
import java.util.regex.*;
public final class RuntimeEfficiencyTest {
    static void check(boolean x,String m){if(!x)throw new AssertionError(m);}
    public static void main(String[] args)throws Exception {
        BoundedTextCache cache=new BoundedTextCache(2,28);
        cache.put("a","first");cache.put("b","second");check(cache.get("a").equals("first"),"cache hit");
        cache.put("c","third");check(!cache.containsKey("b")&&cache.size()==2,"LRU eviction");
        cache.put("large","this entry is too large");check(cache.size()==2&&cache.retainedTextBytes()<=28,"byte bound");
        cache.put("a","x");check(cache.retainedTextBytes()==16,"replacement byte accounting");
        cache.clear();check(cache.size()==0&&cache.retainedTextBytes()==0,"cache invalidation");
        String[][] cases={{"^foo.*$","foo"},{"foo?","fo"},{"foo*","fo"},{"foo{0,2}","fo"},{"foo|bar",""},{"(?i)Foo",""},{"^金币：(.*)$","金币："},{"a\\.b.*","a.b"},{"\\d+金币",""}};
        for(String[] row:cases)check(RegexPrefix.of(row[0]).equals(row[1]),row[0]);
        String[] patterns={"a*","ab?","foo|bar","^.*$","a(bc)?","[ab]*","(?i)Abc","ab{0,2}","ab+","a\\.b.*","金币：(.*)","(?>a|b)c"};
        String[] samples={"","a","b","ab","abb","abc","ac","ABC","a.b123","foo","bar","金币：42"};
        for(String p:patterns)for(String value:samples)if(Pattern.matches(p,value))check(value.startsWith(RegexPrefix.of(p)),"unsafe prefix: "+p);
        Path dir=Files.createTempDirectory(Paths.get(args[0]),"music-stamp-");Path audio=dir.resolve("MainMenu.ogg");
        try {
            Files.write(audio,new byte[]{1,2,3});String first=MusicStamp.of("MainMenu.ogg",audio.toFile(),"hash1");
            check(first!=null&&first.equals(MusicStamp.of("MainMenu.ogg",audio.toFile(),"hash1")),"unchanged audio receipt");
            check(!first.equals(MusicStamp.of("MainMenu.ogg",audio.toFile(),"hash2")),"revision change");
            check(MusicStamp.of("Day.mp3",audio.toFile(),"hash1")!=null,"MP3 supported");
            for(String name:new String[]{"translations.json","LawnStrings.json","global-metadata.dat","playerData.json","../Day.mp3"})check(MusicStamp.of(name,audio.toFile(),"hash1")==null,"non-audio receipt: "+name);
            Files.write(audio,new byte[]{1,2,3,4});check(!first.equals(MusicStamp.of("MainMenu.ogg",audio.toFile(),"hash1")),"length change");
            String second=MusicStamp.of("MainMenu.ogg",audio.toFile(),"hash1");Files.setLastModifiedTime(audio,java.nio.file.attribute.FileTime.fromMillis(audio.toFile().lastModified()+10000));
            check(!second.equals(MusicStamp.of("MainMenu.ogg",audio.toFile(),"hash1")),"mtime change");
            Files.delete(audio);check(MusicStamp.of("MainMenu.ogg",audio.toFile(),"hash1")==null,"missing audio");
        } finally {Files.deleteIfExists(audio);Files.delete(dir);}
        System.out.println("Regex-prefix semantic guards and audio-only verification receipt checks passed.");
    }
}
