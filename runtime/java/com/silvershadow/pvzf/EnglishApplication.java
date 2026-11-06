package com.silvershadow.pvzf;

import android.app.Application;
import android.os.Build;
import android.util.Log;
import java.io.FileInputStream;
import java.io.IOException;

/** Prepare before every possible Unity Activity entry, including OS restoration. */
public final class EnglishApplication extends Application {
    static String processName() throws IOException {
        if(Build.VERSION.SDK_INT>=28){String name=Application.getProcessName();if(name!=null&&!name.isEmpty())return name;}
        try(FileInputStream input=new FileInputStream("/proc/self/cmdline")){
            byte[] bytes=new byte[256];int count=input.read(bytes),end=0;
            while(end<count&&bytes[end]!=0)end++;
            if(end>0)return new String(bytes,0,end,"UTF-8");
        }
        throw new IOException("Cannot identify game process");
    }
    @Override public void onCreate(){
        super.onCreate();
        try{
            // The isolated :plantbrush process must not load Unity or its PCM.
            if(!getPackageName().equals(processName()))return;
            EnglishActivity.prepareProcess(this);
            Log.i("PvZFEnglish","Game process prepared before Activity startup");
        }catch(Exception|LinkageError e){
            Log.e("PvZFEnglish","English process startup failed",e);
            // Never run Unity with a failed metadata refresh or missing hooks.
            throw new IllegalStateException("English setup did not finish. Your saves are unchanged.",e);
        }
    }
}
