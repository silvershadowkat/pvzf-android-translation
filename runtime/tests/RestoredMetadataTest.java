import com.silvershadow.pvzf.ManagedFiles;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Exercises backup restoration using metadata from the actual signed APK pair. */
public final class RestoredMetadataTest {
    private static final String ENTRY="assets/bin/Data/Managed/Metadata/global-metadata.dat";
    static void check(boolean result,String message){if(!result)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception {
        Path workspace=Paths.get(args[0]).toRealPath();
        Path fixture=Files.createTempDirectory(workspace,"restored-metadata-");
        check(fixture.toRealPath().getParent().equals(workspace),"Unexpected fixture directory");
        int repairs=0;
        try(ZipFile seed=new ZipFile(args[1]);ZipFile latest=new ZipFile(args[2])) {
            Path source=fixture.resolve("latest-metadata.dat");
            try(InputStream input=latest.getInputStream(latest.getEntry(ENTRY))){Files.copy(input,source);}
            String expected=ManagedFiles.sha(source.toFile());
            for(String location:new String[]{"external-files","internal-files"}) {
                Path root=Files.createDirectory(fixture.resolve(location));
                Path target=root.resolve("il2cpp/Metadata/global-metadata.dat");
                Files.createDirectories(target.getParent());
                Path player=root.resolve("player-save.bin"),revision=root.resolve("completed-revision");
                byte[] saved="Keep all player progress".getBytes("UTF-8");
                Files.write(player,saved);Files.write(revision,"already current".getBytes("UTF-8"));
                for(int restore=0;restore<2;restore++) {
                    // Second pass restores an old backup AFTER a successful refresh.
                    try(InputStream input=seed.getInputStream(seed.getEntry(ENTRY))){Files.copy(input,target,StandardCopyOption.REPLACE_EXISTING);}
                    check(!expected.equals(ManagedFiles.sha(target.toFile())),"Fixture is not stale");
                    ManagedFiles.replace(root.toFile(),target.toFile(),expected,
                        ()->latest.getInputStream(latest.getEntry(ENTRY)),
                        (from,to)->Files.move(from.toPath(),to.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE));
                    check(expected.equals(ManagedFiles.sha(target.toFile())),"Restored metadata was not repaired");
                    check(Arrays.equals(saved,Files.readAllBytes(player)),"Player data changed");
                    check(new String(Files.readAllBytes(revision),"UTF-8").equals("already current"),"Revision fixture changed");
                    check(!Files.exists(Paths.get(target+".english-new")),"Temporary file leaked");
                    repairs++;
                }
            }
            System.out.println("Actual APK metadata restore checks passed: "+repairs+"; external and internal paths; repeated old-backup restoration; player fixtures preserved.");
        } finally {
            // Only this test's newly created, verified child directory is removed.
            try(java.util.stream.Stream<Path> paths=Files.walk(fixture)) {
                paths.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new UncheckedIOException(e);}});
            }
        }
    }
}
