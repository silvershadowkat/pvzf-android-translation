"""Deterministic failure/lifecycle tests of the real Java bridges with Android fakes.

These exercise scheduling and ownership, not device codec or Binder performance.
"""
import argparse, subprocess
from pathlib import Path

FAKES = {
'android/os/Looper.java': '''package android.os; public class Looper {
 public static final Looper MAIN=new Looper(); public static Looper current;
 public static Looper getMainLooper(){return MAIN;}
}''',
'android/os/SystemClock.java': '''package android.os; public class SystemClock {public static long now=1;public static long elapsedRealtime(){return now;}}''',
'android/os/HandlerThread.java': '''package android.os; public class HandlerThread {final Looper loop=new Looper();public HandlerThread(String s,int p){}public void start(){}public Looper getLooper(){return loop;}}''',
'android/os/Handler.java': '''package android.os; import java.util.*; public class Handler {
 static class Job {Looper l;Runnable r;long at;Job(Looper l,Runnable r,long at){this.l=l;this.r=r;this.at=at;}}
 static final List<Job> jobs=new ArrayList<>();final Looper loop;
 public Handler(Looper l){loop=l;} public boolean post(Runnable r){return postDelayed(r,0);}
 public boolean postDelayed(Runnable r,long t){jobs.add(new Job(loop,r,SystemClock.now+t));return true;}
 public void removeCallbacks(Runnable r){jobs.removeIf(j->j.r==r);}
 public static void drain(){int count=0;while(true){Job next=null;for(Job j:jobs)if(j.at<=SystemClock.now&&(next==null||j.at<next.at))next=j;if(next==null)return;if(++count>1000)throw new AssertionError("Runaway queue");jobs.remove(next);Looper.current=next.l;next.r.run();Looper.current=null;}}
 public static void advance(long t){SystemClock.now+=t;drain();}
}''',
'android/os/Process.java': '''package android.os; public class Process {public static final int THREAD_PRIORITY_BACKGROUND=10;}''',
'android/os/Bundle.java': '''package android.os; public class Bundle {}''',
'android/os/Build.java': '''package android.os; public class Build {public static class VERSION {public static int SDK_INT=35;}}''',
'android/os/IBinder.java': '''package android.os; public interface IBinder {boolean transact(int c,Parcel in,Parcel out,int flags) throws Exception;}''',
'android/os/Parcel.java': '''package android.os; public class Parcel {public int result; public static Parcel obtain(){return new Parcel();}public void writeInterfaceToken(String s){}public void readException(){}public int readInt(){return result;}public void recycle(){}}''',
'android/util/Log.java': '''package android.util; public class Log {public static int w(String t,String s){return 0;}public static int w(String t,String s,Throwable e){return 0;}}''',
'android/content/Intent.java': '''package android.content; public class Intent {public Intent setClassName(Context c,String s){return this;}}''',
'android/content/ComponentName.java': '''package android.content; public class ComponentName {}''',
'android/content/ServiceConnection.java': '''package android.content; import android.os.IBinder; public interface ServiceConnection {void onServiceConnected(ComponentName n,IBinder b);void onServiceDisconnected(ComponentName n);default void onBindingDied(ComponentName n){}default void onNullBinding(ComponentName n){}}''',
'android/content/res/AssetManager.java': '''package android.content.res; import java.io.*; public class AssetManager {public InputStream open(String s)throws IOException{return new ByteArrayInputStream(new byte[0]);}}''',
'android/content/Context.java': '''package android.content; import java.io.*; import android.content.res.AssetManager; public class Context {
 public static final int BIND_AUTO_CREATE=1;public ServiceConnection connection;public int binds,unbinds;
 public File getFilesDir(){return new File("private");}public Context getApplicationContext(){return this;}public AssetManager getAssets(){return new AssetManager();}
 public boolean bindService(Intent i,ServiceConnection c,int flags){if(android.os.Looper.current!=android.os.Looper.MAIN)throw new AssertionError("Bind outside main");connection=c;binds++;return true;}
 public void unbindService(ServiceConnection c){unbinds++;}
}''',
'android/app/Activity.java': '''package android.app; public class Activity {}''',
'android/app/Application.java': '''package android.app; import android.os.Bundle; public class Application extends android.content.Context {
 public final java.util.List<ActivityLifecycleCallbacks> callbacks=new java.util.ArrayList<>();
 public void registerActivityLifecycleCallbacks(ActivityLifecycleCallbacks c){callbacks.add(c);}
 public interface ActivityLifecycleCallbacks {void onActivityCreated(Activity a,Bundle b);void onActivityStarted(Activity a);void onActivityResumed(Activity a);void onActivityPaused(Activity a);void onActivityStopped(Activity a);void onActivityDestroyed(Activity a);void onActivitySaveInstanceState(Activity a,Bundle b);}
}''',
'android/media/MediaPlayer.java': '''package android.media; import java.util.*; import android.os.*; public class MediaPlayer {
 public interface OnErrorListener{boolean onError(MediaPlayer p,int what,int extra);} public interface OnPreparedListener{void onPrepared(MediaPlayer p);} public interface OnSeekCompleteListener{void onSeekComplete(MediaPlayer p);}
 public static final List<MediaPlayer> all=new ArrayList<>();public boolean released;public int starts,pauses,seeks,position;public float volume;public String source;
 public OnErrorListener error;public OnPreparedListener prepared;public OnSeekCompleteListener seek;
 final Looper owner=Looper.current;
 public MediaPlayer(){if(Looper.current==null||Looper.current==Looper.MAIN)throw new AssertionError("Music created on caller/UI thread");all.add(this);}
 public void release(){released=true;}public void setLooping(boolean b){}public void setOnErrorListener(OnErrorListener l){error=l;}public void setOnPreparedListener(OnPreparedListener l){prepared=l;}public void setOnSeekCompleteListener(OnSeekCompleteListener l){seek=l;}
 public void setDataSource(String s){source=s;}public void prepareAsync(){}public int getDuration(){return 60000;}
 public void seekTo(int n){if(released)throw new AssertionError("Use after release");seeks++;position=n;}
 public void start(){if(released)throw new AssertionError("Start released player");starts++;}public void pause(){pauses++;}public void setVolume(float a,float b){volume=a;}
 public void complete(){Looper.current=owner;try{prepared.onPrepared(this);}finally{Looper.current=null;}}public void seekComplete(){Looper.current=owner;try{seek.onSeekComplete(this);}finally{Looper.current=null;}}
}'''
}
TEST = '''import android.app.*;import android.os.*;import android.media.*;import android.content.*;
import com.silvershadow.pvzf.*;
public class AsyncBridgeTest {
 static int checks;static void ok(boolean x,String message){checks++;if(!x)throw new AssertionError(message);}
 static MediaPlayer last(){return MediaPlayer.all.get(MediaPlayer.all.size()-1);}
 public static void main(String[] args)throws Exception {
  java.nio.file.Path model=java.nio.file.Files.createTempFile(java.nio.file.Paths.get(args[0]),"model-receipt-",".onnx");
  try {
   java.nio.file.Files.write(model,new byte[]{1,2,3});String stamp=ModelStamp.of("vision.onnx",model.toFile(),"hash1");
   ok(stamp!=null&&stamp.equals(ModelStamp.of("vision.onnx",model.toFile(),"hash1")),"Unchanged private model receipt");
   ok(!stamp.equals(ModelStamp.of("vision.onnx",model.toFile(),"hash2")),"Model revision invalidates receipt");
   java.nio.file.Files.write(model,new byte[]{1,2,3,4});ok(!stamp.equals(ModelStamp.of("vision.onnx",model.toFile(),"hash1")),"Model file change invalidates receipt");
   ok(ModelStamp.of("playerData.json",model.toFile(),"hash1")==null,"No receipts for saves or arbitrary files");
  } finally {java.nio.file.Files.delete(model);}
  Application app=new Application();MusicBridge.init(app);
  ok(MusicBridge.sync(0,"../../save",true,1,0,0)==-1,"Reject arbitrary files");
  ok(MusicBridge.sync(0,"Pool",true,.6f,3,1)==1,"Preparing status");
  ok(MediaPlayer.all.isEmpty(),"No decode on caller thread");Handler.drain();MediaPlayer pool=last();
  pool.complete();ok(pool.seeks==1&&pool.position==3000&&pool.starts==0,"Seek once before first play");pool.seekComplete();
  ok(pool.starts==1,"Start after prepare and seek");
  for(int i=0;i<20;i++){MusicBridge.sync(0,"Pool",true,.4f,3+i,1);Handler.drain();}
  ok(pool.seeks==1&&pool.starts==1&&pool.volume==.4f,"Polling never restarts or seeks the song");
  Activity game=new Activity();Application.ActivityLifecycleCallbacks music=app.callbacks.get(0);
  music.onActivityResumed(game);Handler.drain();music.onActivityPaused(game);Handler.drain();
  ok(pool.pauses==1,"Pause in background");music.onActivityResumed(game);Handler.drain();ok(pool.starts==2&&pool.seeks==1,"Resume without restart");
  MusicBridge.sync(1,"Pool_drum",true,1,3,1);Handler.drain();MediaPlayer drum=last();drum.complete();drum.seekComplete();
  ok(MediaPlayer.all.stream().filter(p->!p.released).count()==2,"Only two streams");
  MusicBridge.sync(0,"Night",true,1,0,2);Handler.drain();MediaPlayer night=last();
  ok(pool.released,"Old stream released");pool.complete();pool.seekComplete();ok(pool.starts==2,"Late callbacks cannot restart old track");
  night.error.onError(night,1,2);ok(MusicBridge.sync(0,"Night",true,1,0,2)==-1,"Decoder failure surfaced for original fallback");Handler.drain();
  int count=MediaPlayer.all.size();for(int i=0;i<10;i++){MusicBridge.sync(0,"Night",true,1,0,2);Handler.drain();}ok(MediaPlayer.all.size()==count,"No decoder retry loop");
  MusicBridge.sync(0,"",false,0,0,2);MusicBridge.sync(1,"",false,0,0,1);Handler.drain();ok(drum.released,"Original selection releases streams");
  MusicBridge.sync(0,"Night",true,1,0,2);Handler.drain();MediaPlayer retry=last();ok(retry!=night,"Explicit toggle retries");
  Handler.advance(15001);ok(retry.released&&MusicBridge.sync(0,"Night",true,1,0,2)==-1,"Prepare timeout falls back");Handler.drain();
  // A quick track change before preparation completes must never start stale music.
  MusicBridge.sync(0,"Day",true,1,0,3);Handler.drain();MediaPlayer day=last();MusicBridge.sync(0,"Roof",true,1,0,4);day.complete();Handler.drain();
  ok(day.released&&day.starts==0,"Queued track change wins over stale prepared callback");
  MusicBridge.sync(0,"",false,0,0,4);Handler.drain();
  PlantbrushBridge.init(app);ok(PlantbrushBridge.request()==1&&app.binds==0,"Plantbrush request never waits for bind");Handler.drain();
  ServiceConnection first=app.connection;first.onServiceConnected(new ComponentName(),(c,in,out,f)->{ok(Looper.current!=Looper.MAIN,"Health Binder off main");out.result=2;return true;});
  Handler.advance(1000);ok(PlantbrushBridge.status()==2,"Recognizer ready cached");
  first.onServiceDisconnected(new ComponentName());ok(PlantbrushBridge.status()==-1&&app.unbinds==1,"Death releases binding");
  ok(PlantbrushBridge.request()==-1,"Bounded retry cooldown");Handler.advance(3001);ok(PlantbrushBridge.request()==1,"Explicit retry without game restart");Handler.drain();
  ok(app.binds==2&&app.connection!=first,"Fresh connection per attempt");first.onBindingDied(new ComponentName());ok(PlantbrushBridge.status()==1,"Ignore stale death callback");
  Handler.advance(120001);ok(PlantbrushBridge.status()==-1&&app.unbinds==2,"Startup timeout closes session");
  Handler.advance(3001);PlantbrushBridge.request();Handler.drain();app.connection.onServiceConnected(new ComponentName(),(c,in,out,f)->{out.result=2;return true;});Handler.advance(1000);
  PlantbrushBridge.leave();Handler.drain();ok(PlantbrushBridge.status()==0&&app.unbinds==3,"Leaving frees recognizer");
  System.out.println(checks+" async music/recognizer checks passed");
 }
}'''

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--jdk',type=Path,required=True)
    a=ap.parse_args();a.work.mkdir(parents=True,exist_ok=True)
    sources=[]
    for name,code in {**FAKES,'AsyncBridgeTest.java':TEST}.items():
        p=a.work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(code,encoding='utf8');sources.append(p)
    r=Path(__file__).resolve().parents[1]
    sources += [r/'runtime/java/com/silvershadow/pvzf'/name for name in ('MusicBridge.java','PlantbrushBridge.java')]
    sources.append(r/'runtime/plantbrush/java/com/silvershadow/pvzf/ModelStamp.java')
    classes=a.work/'classes';classes.mkdir(exist_ok=True)
    subprocess.run([str(a.jdk/'bin/javac.exe'),'-encoding','UTF-8','-d',str(classes),*map(str,sources)],check=True,timeout=60)
    subprocess.run([str(a.jdk/'bin/java.exe'),'-XX:ActiveProcessorCount=2','-cp',str(classes),'AsyncBridgeTest',str(a.work)],check=True,timeout=30)
if __name__=='__main__':main()
