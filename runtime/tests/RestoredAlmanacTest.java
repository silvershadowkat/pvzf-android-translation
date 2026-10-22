import com.silvershadow.pvzf.ManagedFiles;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Verify real APK almanac overrides across default and named save profiles. */
public final class RestoredAlmanacTest {
    static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    static void copy(ZipFile apk,String name,Path target)throws Exception {
        Files.createDirectories(target.getParent());
        try(InputStream in=apk.getInputStream(apk.getEntry("assets/english-almanac/"+name))){Files.copy(in,target,StandardCopyOption.REPLACE_EXISTING);}
    }
    public static void main(String[] args)throws Exception {
        Path workspace=Paths.get(args[0]).toRealPath(),fixture=Files.createTempDirectory(workspace,"restored-almanac-");
        check(fixture.toRealPath().getParent().equals(workspace),"Unexpected fixture directory");
        String[] names={"LawnStrings.json","ZombieStrings.json","DetailStrings.json"};int repaired=0;
        try(ZipFile seed=new ZipFile(args[1]);ZipFile latest=new ZipFile(args[2])) {
            Map<String,String> hashes=new HashMap<>();
            for(String name:names){Path source=fixture.resolve("source/"+name);copy(latest,name,source);hashes.put(name,ManagedFiles.sha(source.toFile()));}
            for(String storage:new String[]{"external-files","internal-files"}) {
                Path root=Files.createDirectory(fixture.resolve(storage));
                List<Path> profiles=Arrays.asList(root,root.resolve("Saves/Alice"),root.resolve("Saves/Second profile"));
                Map<Path,byte[]> preserved=new HashMap<>();
                for(String file:new String[]{"playerData.json","config.json","Saves/Alice/AutoChessSaves/slot1.json","Saves/Alice/AutoChessSaves/slot2.json","Saves/Second profile/autosave.json","Saves/No language override/playerData.json","unknown.json"}) {
                    Path path=root.resolve(file);Files.createDirectories(path.getParent());byte[] bytes=("saved:"+file).getBytes("UTF-8");Files.write(path,bytes);preserved.put(path,bytes);
                }
                for(Path profile:profiles)for(String name:names)copy(seed,name,profile.resolve(name));
                for(int pass=0;pass<2;pass++) {
                    for(Path profile:profiles) {
                        copy(seed,"LawnStrings.json",profile.resolve("LawnStrings.json"));
                        check(!hashes.get("LawnStrings.json").equals(ManagedFiles.sha(profile.resolve("LawnStrings.json").toFile())),"Seed plant name was not stale");
                    }
                    ManagedFiles.refreshAlmanacs(root.toFile(),hashes,
                        name->latest.getInputStream(latest.getEntry("assets/english-almanac/"+name)),
                        (from,to)->Files.move(from.toPath(),to.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE),false);
                    for(Path profile:profiles){for(String name:names)check(hashes.get(name).equals(ManagedFiles.sha(profile.resolve(name).toFile())),"Stale almanac: "+name);repaired++;}
                    for(Map.Entry<Path,byte[]> entry:preserved.entrySet())check(Arrays.equals(entry.getValue(),Files.readAllBytes(entry.getKey())),"Save changed: "+entry.getKey());
                    for(String name:names)check(!Files.exists(root.resolve("Saves/No language override/"+name)),"Main created an unnecessary override");
                }
                Map<String,String> invalid=new HashMap<>(hashes);invalid.put("playerData.json",hashes.get("LawnStrings.json"));
                try{ManagedFiles.refreshAlmanacs(root.toFile(),invalid,name->{throw new AssertionError("Unexpected read");},(from,to)->{throw new AssertionError("Unexpected write");},false);throw new AssertionError("Accepted a save file in the language inventory");}catch(IOException expected){}
            }
            System.out.println("Actual APK almanac restore checks passed: "+repaired+"; two storage roots, three profiles, repeated old-backup restoration; all save fixtures preserved; absent overrides left absent; unexpected filenames rejected.");
        } finally {
            try(java.util.stream.Stream<Path> paths=Files.walk(fixture)){paths.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new UncheckedIOException(e);}});}
        }
    }
}
