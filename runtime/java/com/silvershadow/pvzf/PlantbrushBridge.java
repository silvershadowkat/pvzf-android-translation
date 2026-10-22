package com.silvershadow.pvzf;

import android.app.*;
import android.content.*;
import android.os.*;
import android.util.Log;

/** Optional AI variant bridge. A private bound process owns all model memory. */
public final class PlantbrushBridge implements Application.ActivityLifecycleCallbacks {
    private static final Handler main=new Handler(Looper.getMainLooper());
    private static Context context;
    private static volatile int state; // 0 absent, 1 starting, 2 ready, -1 failed
    private static boolean installed,bound;
    private static volatile boolean requested;
    private static final java.util.Set<Activity> visible=java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<Activity,Boolean>());
    private static IBinder remote;
    private static long deadline;
    private static final Runnable release=()->stop();
    public static void init(Context c) {
        if(context!=null)return;
        context=c.getApplicationContext();
        try(java.io.InputStream in=context.getAssets().open("plantbrush/manifest.json")){installed=true;}
        catch(java.io.IOException absent){return;}
        ((Application)context).registerActivityLifecycleCallbacks(new PlantbrushBridge());
    }
    private static final ServiceConnection connection=new ServiceConnection(){
        public void onServiceConnected(ComponentName n,IBinder b){remote=b;poll();}
        public void onServiceDisconnected(ComponentName n){remote=null;state=-1;stopBinding();Log.w("PvZFPlantbrush","Recognition process disconnected; no automatic restart");}
        public void onBindingDied(ComponentName n){remote=null;state=-1;stopBinding();}
        public void onNullBinding(ComponentName n){state=-1;stopBinding();}
    };
    private static void poll(){
        if(!requested||remote==null)return;
        Parcel in=Parcel.obtain(),out=Parcel.obtain();
        try{
            in.writeInterfaceToken("com.silvershadow.pvzf.Plantbrush");
            if(!remote.transact(1,in,out,0))throw new RemoteException("No status");
            out.readException();state=out.readInt();
        }catch(Exception e){state=-1;Log.w("PvZFPlantbrush","Recognition status unavailable",e);}
        finally{in.recycle();out.recycle();}
        if(state==1&&SystemClock.elapsedRealtime()<deadline)main.postDelayed(PlantbrushBridge::poll,250);
        else if(state==1){state=-1;stopBinding();}
        else if(state<0)stopBinding();
    }
    /** Never performs disk IO, waits for model loading, or invokes inference on Unity's thread. */
    public static int request(){
        if(!installed)return 0;
        if(Build.VERSION.SDK_INT<26)return -1;
        main.removeCallbacks(release);
        if(!requested){requested=true;state=1;main.post(()->{
            deadline=SystemClock.elapsedRealtime()+120000;
            if(!requested)return;
            try{bound=context.bindService(new Intent().setClassName(context,"com.silvershadow.pvzf.PlantbrushService"),connection,Context.BIND_AUTO_CREATE);if(!bound)state=-1;}
            catch(Exception e){state=-1;Log.e("PvZFPlantbrush","Cannot start recognition",e);}
        });}
        return state;
    }
    private static void stopBinding(){if(bound){context.unbindService(connection);bound=false;}remote=null;}
    private static void stop(){requested=false;state=0;stopBinding();}
    public static void leave(){main.post(()->{main.removeCallbacks(release);stop();});}
    public void onActivityStarted(Activity a){visible.add(a);main.removeCallbacks(release);}
    public void onActivityStopped(Activity a){visible.remove(a);if(visible.isEmpty()){main.postDelayed(release,30000);}}
    public void onActivityCreated(Activity a,Bundle b){}
    public void onActivityDestroyed(Activity a){}
    public void onActivityResumed(Activity a){}
    public void onActivityPaused(Activity a){}
    public void onActivitySaveInstanceState(Activity a,Bundle b){}
}
