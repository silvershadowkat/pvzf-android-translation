import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
public final class RegexReview {
    public static void main(String[] args)throws Exception {
        int n=0;Pattern slots=Pattern.compile("\\{(\\d+)\\}");
        for(String row:Files.readAllLines(Paths.get(args[0]))) {
            String[] parts=row.split("\\t",-1);String p=new String(Base64.getDecoder().decode(parts[0]),"UTF-8"),r=new String(Base64.getDecoder().decode(parts[1]),"UTF-8");
            Pattern compiled=Pattern.compile(p);Matcher m=slots.matcher(r);
            while(m.find())if(Integer.parseInt(m.group(1))>=compiled.matcher("").groupCount())throw new AssertionError("Missing capture: "+p);
            n++;
        }
        System.out.println("Java regex syntax and capture checks passed: "+n);
    }
}
