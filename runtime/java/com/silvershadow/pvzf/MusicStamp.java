package com.silvershadow.pvzf;
import java.io.File;

/** Receipt optimization for immutable app-owned audio only, never language/save data. */
public final class MusicStamp {
    public static String of(String name,File file,String expectedHash) {
        if(!name.matches("[A-Za-z0-9_-]+\\.(?:ogg|mp3)") || !file.isFile() || !file.canRead()
            || file.length()==0 || file.lastModified()<=0)return null;
        try {if(!file.getCanonicalFile().equals(file.getAbsoluteFile()))return null;}
        catch(java.io.IOException invalid){return null;}
        return expectedHash+":"+file.length()+":"+file.lastModified();
    }
}
