package com.silvershadow.pvzf;

import android.app.*;
import android.content.Context;
import android.media.MediaPlayer;
import android.os.*;
import android.util.Log;
import java.io.File;
import java.util.*;

/** Two bounded, asynchronous music streams. Never decodes a song on Unity's thread. */
public final class MusicBridge implements Application.ActivityLifecycleCallbacks {
    private static final String TAG="PvZFMusic";
    private static final Set<String> TRACKS=new HashSet<>(Arrays.asList(
        "Boss2","Day_drum","Day","Fog_drum","Fog","Garden","IZ","MainMenu",
        "Night_drum","Night","Pool_drum","Pool","Roof_drum","Roof_pre","Roof","SelectCard","UltimateBattle"));
    private static final Slot[] slots={new Slot(),new Slot()};
    private static Handler worker;
    private static File root;
    private static volatile boolean foreground=true;
    private static final Set<Activity> resumed=Collections.newSetFromMap(new IdentityHashMap<Activity,Boolean>());
    private static final class Slot {
        // Synchronize only tiny snapshots, never hold this lock during MediaPlayer calls.
        String wanted=""; boolean wantedPlaying; float wantedVolume; int position,epoch; long observed;
        boolean queued; volatile int state; // 0 off, 1 preparing, 2 ready, -1 failed
        MediaPlayer player; String loaded=""; int loadedEpoch; boolean ready,playing;
        boolean seekPending;
    }
    public static synchronized void init(Context c) {
        if(worker!=null)return;
        root=new File(c.getFilesDir(),"english-runtime");
        HandlerThread thread=new HandlerThread("BloomsMusic",android.os.Process.THREAD_PRIORITY_BACKGROUND);
        thread.start();worker=new Handler(thread.getLooper());
        ((Application)c.getApplicationContext()).registerActivityLifecycleCallbacks(new MusicBridge());
    }
    /** Called at most four times per second per channel, plus explicit track changes. */
    public static int sync(int index,String track,boolean playing,float volume,float seconds,int epoch) {
        if(worker==null||index<0||index>=slots.length)return -1;
        if(!track.isEmpty()&&!TRACKS.contains(track))return -1;
        Slot s=slots[index];
        synchronized(s) {
            if(!s.wanted.equals(track)||s.epoch!=epoch)s.state=track.isEmpty()?0:1;
            s.position=(int)(Math.max(0,Math.min(seconds,86400))*1000);s.observed=SystemClock.elapsedRealtime();
            s.wanted=track;s.wantedPlaying=playing;s.wantedVolume=Math.max(0,Math.min(volume,1));s.epoch=epoch;
            if(!s.queued){s.queued=true;worker.post(()->apply(s));}
            return s.state;
        }
    }
    private static void release(Slot s) {
        MediaPlayer p=s.player;s.player=null;s.ready=false;s.playing=false;s.seekPending=false;
        if(p!=null){try{p.release();}catch(RuntimeException ignored){}}
    }
    private static void fail(Slot s,MediaPlayer p,String why) {
        if(s.player!=p)return;
        Log.w(TAG,why+": "+s.loaded);release(s);
        synchronized(s){if(s.loaded.equals(s.wanted)&&s.loadedEpoch==s.epoch)s.state=-1;}
    }
    private static void apply(Slot s) {
        String track; boolean play; float volume; int epoch,position;
        synchronized(s){s.queued=false;track=s.wanted;play=s.wantedPlaying;volume=s.wantedVolume;epoch=s.epoch;position=s.position;}
        if(!track.equals(s.loaded)||epoch!=s.loadedEpoch){
            release(s);s.loaded=track;s.loadedEpoch=epoch;
            if(!track.isEmpty())prepare(s,track,position);
        }
        MediaPlayer p=s.player;
        if(p==null||!s.ready||s.seekPending)return;
        try {
            p.setVolume(volume,volume);
            boolean shouldPlay=play&&foreground;
            if(shouldPlay&&!s.playing){p.start();s.playing=true;}
            else if(!shouldPlay&&s.playing){p.pause();s.playing=false;}
        }catch(RuntimeException error){fail(s,p,"Playback failed; using original music");}
    }
    private static void prepare(Slot s,String track,int position) {
        final MediaPlayer p;
        try{p=new MediaPlayer();}catch(RuntimeException error){s.state=-1;Log.w(TAG,"Cannot allocate music player",error);return;}
        s.player=p;
        try {
            // Game music channels loop; the game's stop/track changes still govern these streams.
            p.setLooping(true);
            p.setOnErrorListener((player,what,extra)->{fail(s,player,"Decoder error "+what+"/"+extra);return true;});
            p.setOnSeekCompleteListener(player->{if(s.player==player){s.seekPending=false;apply(s);}});
            p.setOnPreparedListener(player->{
                if(s.player!=player)return;
                s.ready=true;
                synchronized(s){if(s.loaded.equals(s.wanted)&&s.loadedEpoch==s.epoch)s.state=2;}
                try {
                    int length=player.getDuration();long nowPosition;
                    synchronized(s){nowPosition=s.position+(s.wantedPlaying?SystemClock.elapsedRealtime()-s.observed:0);}
                    if(nowPosition>0&&length>0){s.seekPending=true;player.seekTo((int)(nowPosition%length));}
                    else apply(s);
                }catch(RuntimeException error){fail(s,player,"Preparing playback failed");}
            });
            p.setDataSource(new File(root,track+((track.equals("MainMenu")||track.equals("Garden"))?".ogg":".mp3")).getAbsolutePath());
            p.prepareAsync();
            worker.postDelayed(()->{if(s.player==p&&(!s.ready||s.seekPending))fail(s,p,"Music prepare timed out");},15000);
        }catch(Exception error){fail(s,p,"Music unavailable; using original music");}
    }
    private static void refreshForeground(boolean value){foreground=value;if(worker!=null)worker.post(()->{for(Slot s:slots)apply(s);});}
    public void onActivityResumed(Activity a){resumed.add(a);refreshForeground(true);}
    public void onActivityPaused(Activity a){resumed.remove(a);if(resumed.isEmpty())refreshForeground(false);}
    public void onActivityCreated(Activity a,Bundle b){}
    public void onActivityStarted(Activity a){}
    public void onActivityStopped(Activity a){}
    public void onActivityDestroyed(Activity a){}
    public void onActivitySaveInstanceState(Activity a,Bundle b){}
}
