package com.silvershadow.pvzf;

import java.io.*;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;
import java.util.Arrays;
import java.util.HashSet;

/** Small host-testable refresh primitive. Caller supplies exact owned paths. */
public final class ManagedFiles {
    public interface Opener { InputStream open() throws Exception; }
    public interface Renamer { void rename(File from, File to) throws Exception; }
    public interface AssetOpener { InputStream open(String name) throws Exception; }
    private static final String[] ALMANACS={"LawnStrings.json","ZombieStrings.json","DetailStrings.json"};
    /** Refresh only the three verified language overrides, never any save content. */
    public static void refreshAlmanacs(File root,Map<String,String> hashes,AssetOpener source,Renamer rename,boolean seed) throws Exception {
        if(!hashes.keySet().equals(new HashSet<String>(Arrays.asList(ALMANACS))))throw new IOException("Unexpected almanac file inventory");
        refreshAlmanacDirectory(root,root,hashes,source,rename,seed);
        // SaveInfo.GetDataPath uses persistentDataPath/Saves/playerName
        // for named profiles. Enumerate immediate profile directories only.
        File saves=new File(root,"Saves");
        if(!saves.exists())return;
        if(!saves.getCanonicalPath().equals(root.getCanonicalPath()+File.separator+"Saves"))throw new IOException("Save profile directory contains an alias");
        File[] profiles=saves.listFiles(File::isDirectory);
        if(profiles==null)throw new IOException("Cannot inspect profile language overrides");
        for(File profile:profiles) {
            if(!profile.getCanonicalPath().equals(saves.getCanonicalPath()+File.separator+profile.getName()))throw new IOException("Save profile contains an alias");
            refreshAlmanacDirectory(root,profile,hashes,source,rename,seed);
        }
    }
    private static void refreshAlmanacDirectory(File root,File directory,Map<String,String> hashes,AssetOpener source,Renamer rename,boolean seed) throws Exception {
        for(String name:ALMANACS) {
            File target=new File(directory,name);
            if(target.exists() || (seed && name.equals("LawnStrings.json")))
                replace(root,target,hashes.get(name),()->source.open(name),rename);
        }
    }
    public static String sha(File file) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(InputStream in=new FileInputStream(file)) {
            byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)digest.update(b,0,n);
        }
        StringBuilder s=new StringBuilder();for(byte b:digest.digest())s.append(String.format(Locale.ROOT,"%02x",b&255));return s.toString();
    }
    public static void replace(File root, File target, String expected, Opener source, Renamer renamer) throws Exception {
        String base=root.getCanonicalPath()+File.separator;
        String lexical=root.getAbsolutePath()+File.separator;
        if(!target.getAbsolutePath().startsWith(lexical))throw new IOException("Managed path escapes game storage");
        String relative=target.getAbsolutePath().substring(lexical.length());
        if(!target.getCanonicalPath().equals(base+relative))throw new IOException("Managed path contains an alias");
        if(target.isFile() && expected.equals(sha(target)))return;
        File parent=target.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("Cannot create managed directory");
        File tmp=new File(parent,target.getName()+".english-new");
        if(!tmp.getCanonicalPath().equals(target.getCanonicalPath()+".english-new"))throw new IOException("Temporary path contains an alias");
        try {
            try(InputStream in=source.open();FileOutputStream out=new FileOutputStream(tmp)) {
                byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);out.getFD().sync();
            }
            if(!expected.equals(sha(tmp)))throw new IOException("Managed asset hash mismatch");
            renamer.rename(tmp,target);
        } finally {if(tmp.exists())tmp.delete();}
    }
}
