import com.silvershadow.pvzf.ManagedFiles;
import java.io.*;
import java.nio.file.*;
import java.util.*;
public final class ManagedFilesTest {
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    static void write(Path p,String text)throws Exception{Files.createDirectories(p.getParent());Files.write(p,text.getBytes("UTF-8"));}
    static String read(Path p)throws Exception{return new String(Files.readAllBytes(p),"UTF-8");}
    public static void main(String[] args)throws Exception{
        Path root=Files.createTempDirectory(Paths.get(args[0]),"refresh-test-");int passed=0;
        try {
            String[] saves={"playerData.json","level1.json","save1.json","save2.json","autosave.json","Player/Saves/slot-a.json","AutoChessSaves/slot-a.json","AutoChessSaves/slot-b.json","GardenUnifiedData.json","CustomIZ.json","unknown-user-file.bin"};
            for(String s:saves)write(root.resolve(s),"original:"+s);
            Path target=root.resolve("il2cpp/Metadata/global-metadata.dat"),source=root.resolve("test-source");
            write(source,"NEW translations");write(target,"OLD translations");String hash=ManagedFiles.sha(source.toFile());
            ManagedFiles.Opener opener=()->Files.newInputStream(source);
            ManagedFiles.Renamer rename=(from,to)->Files.move(from.toPath(),to.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
            ManagedFiles.replace(root.toFile(),target.toFile(),hash,opener,rename);check(read(target).equals("NEW translations"),"refresh");passed++;
            ManagedFiles.replace(root.toFile(),target.toFile(),hash,()->{throw new AssertionError("unchanged asset opened");},rename);passed++;
            write(target,"OLD translations");
            try{ManagedFiles.replace(root.toFile(),target.toFile(),"bad-hash",opener,rename);throw new AssertionError("accepted bad hash");}catch(IOException expected){}
            check(read(target).equals("OLD translations"),"bad hash damaged old file");passed++;
            try{ManagedFiles.replace(root.toFile(),target.toFile(),hash,opener,(f,t)->{throw new IOException("simulated interruption");});throw new AssertionError("accepted failed rename");}catch(IOException expected){}
            check(read(target).equals("OLD translations"),"rename failure damaged file");passed++;
            ManagedFiles.replace(root.toFile(),target.toFile(),hash,opener,rename);check(read(target).equals("NEW translations"),"retry failed");passed++;
            for(String s:saves)check(read(root.resolve(s)).equals("original:"+s),"save changed: "+s);passed++;
            try{ManagedFiles.replace(root.toFile(),root.resolve("../escape").toFile(),hash,opener,rename);throw new AssertionError("accepted escape");}catch(IOException expected){}passed++;
            check(!Files.exists(Paths.get(target+".english-new")),"temporary file leaked");passed++;
            System.out.println("Managed refresh checks passed: "+passed+"; preserved "+saves.length+" save/settings/unknown fixtures.");
        }finally{
            try(java.util.stream.Stream<Path> entries=Files.walk(root)){
                entries.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new RuntimeException(e);}});
            }
        }
    }
}
