package com.silvershadow.pvzf;

import android.app.*;
import android.content.*;
import android.os.*;
import android.util.Log;

/** Optional, isolated recognizer. Explicit taps can retry a failed session. */
public final class PlantbrushBridge implements Application.ActivityLifecycleCallbacks {
    private static final Handler main=new Handler(Looper.getMainLooper());
    private static Handler health;
    private static Context context;
    private static volatile int state; // 0 absent/idle, 1 starting, 2 ready, -1 failed
    private static volatile long retryAfter;
    private static boolean installed;
    private static Session current; // main thread only
    private static final java.util.Set<Activity> visible=java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<Activity,Boolean>());
    private static final Runnable release=()->stop();
    public static void init(Context c) {
        if(context!=null)return;
        context=c.getApplicationContext();
        try(java.io.InputStream in=context.getAssets().open("plantbrush/manifest.json")){installed=true;}
        catch(java.io.IOException absent){return;}
        HandlerThread thread=new HandlerThread("PlantbrushHealth",android.os.Process.THREAD_PRIORITY_BACKGROUND);
        thread.start();health=new Handler(thread.getLooper());
        ((Application)context).registerActivityLifecycleCallbacks(new PlantbrushBridge());
    }
    private static final class Session implements ServiceConnection,Runnable {
        IBinder remote; boolean bound,polling;
        final long deadline=SystemClock.elapsedRealtime()+120000;
        long lastReply=SystemClock.elapsedRealtime();
        void bind(){
            if(current!=this)return;
            try{bound=context.bindService(new Intent().setClassName(context,"com.silvershadow.pvzf.PlantbrushService"),this,Context.BIND_AUTO_CREATE);if(!bound)fail("Cannot bind recognition");}
            catch(Exception e){fail("Cannot start recognition");Log.w("PvZFPlantbrush","Bind failed",e);}
            if(current==this)main.postDelayed(this,1000);
        }
        public void onServiceConnected(ComponentName n,IBinder b){if(current!=this)return;remote=b;lastReply=SystemClock.elapsedRealtime();}
        public void onServiceDisconnected(ComponentName n){fail("Recognition process disconnected");}
        public void onBindingDied(ComponentName n){fail("Recognition binding died");}
        public void onNullBinding(ComponentName n){fail("Recognition binding unavailable");}
        void close(){main.removeCallbacks(this);remote=null;if(bound){bound=false;try{context.unbindService(this);}catch(IllegalArgumentException ignored){}}}
        void fail(String reason){
            if(current!=this)return;
            current=null;close();retryAfter=SystemClock.elapsedRealtime()+3000;state=-1;
            Log.w("PvZFPlantbrush",reason+"; next tap can restart the recognizer");
        }
        public void run(){
            if(current!=this)return;
            long now=SystemClock.elapsedRealtime();
            if((state==1&&now>deadline)||(state==2&&now-lastReply>10000)){fail("Recognition service timed out");return;}
            final IBinder service=remote;
            if(service!=null&&!polling){
                polling=true;
                // Binder never blocks Unity or Android's UI thread.
                health.post(()->{
                    int result=-1;Parcel in=Parcel.obtain(),out=Parcel.obtain();
                    try{in.writeInterfaceToken("com.silvershadow.pvzf.Plantbrush");if(service.transact(1,in,out,0)){out.readException();result=out.readInt();}}
                    catch(Exception e){Log.w("PvZFPlantbrush","Status unavailable",e);}
                    finally{in.recycle();out.recycle();}
                    final int status=result;
                    main.post(()->{if(current!=this)return;polling=false;lastReply=SystemClock.elapsedRealtime();if(status<1){fail("Recognition unavailable");}else state=status;});
                });
            }
            main.postDelayed(this,state==1?250:1000);
        }
    }
    /** No disk access, waiting, or inference on Unity's thread. No automatic crash loop. */
    public static synchronized int request(){
        if(!installed)return 0;
        if(Build.VERSION.SDK_INT<26)return -1;
        main.removeCallbacks(release);
        if(state==0||(state<0&&SystemClock.elapsedRealtime()>=retryAfter)){
            state=1;
            main.post(()->{if(state!=1)return;if(current!=null)current.close();current=new Session();current.bind();});
        }
        return state;
    }
    public static int status(){return state;}
    private static void stop(){if(current!=null){Session old=current;current=null;old.close();}state=0;}
    public static void leave(){main.post(()->{main.removeCallbacks(release);stop();});}
    public void onActivityStarted(Activity a){visible.add(a);main.removeCallbacks(release);}
    public void onActivityStopped(Activity a){visible.remove(a);if(visible.isEmpty())main.postDelayed(release,30000);}
    public void onActivityCreated(Activity a,Bundle b){}
    public void onActivityDestroyed(Activity a){}
    public void onActivityResumed(Activity a){}
    public void onActivityPaused(Activity a){}
    public void onActivitySaveInstanceState(Activity a,Bundle b){}
}
