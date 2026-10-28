package com.silvershadow.pvzf;
import java.io.File;

/** Receipt for verified, immutable models in the recognizer's app-private directory. */
public final class ModelStamp {
    public static String of(String name,File file,String hash) {
        if(!(name.equals("vision.onnx")||name.equals("index.bin")||name.equals("catalog.json"))
            ||!file.isFile()||!file.canRead()||file.length()==0||file.lastModified()<=0)return null;
        try{if(!file.getCanonicalFile().equals(file.getAbsoluteFile()))return null;}
        catch(java.io.IOException e){return null;}
        return hash+":"+file.length()+":"+file.lastModified();
    }
}
