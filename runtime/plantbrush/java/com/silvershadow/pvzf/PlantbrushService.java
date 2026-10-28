package com.silvershadow.pvzf;

import android.app.Service;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.*;
import android.os.Process;
import android.util.Log;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import org.json.*;

/** Non-exported, bound, separate-process service. No Internet endpoint or cloud fallback. */
public final class PlantbrushService extends Service {
    private volatile int state=1;
    private volatile ServerSocket server;
    private volatile boolean stopped;
    private volatile long requestStarted;
    private PlantbrushRecognizer recognizer;
    private final Binder binder=new Binder(){
        @Override protected boolean onTransact(int code,Parcel in,Parcel out,int flags)throws RemoteException{
            if(code!=1)return super.onTransact(code,in,out,flags);
            in.enforceInterface("com.silvershadow.pvzf.Plantbrush");
            // Binder remains responsive even when native inference is stuck.
            long started=requestStarted;
            int status=started!=0&&SystemClock.elapsedRealtime()-started>45000?-1:state;
            out.writeNoException();out.writeInt(status);return true;
        }
    };
    public IBinder onBind(Intent i){return binder;}
    public void onCreate(){super.onCreate();new Thread(this::run,"PlantbrushWorker").start();}
    private void run(){
        Process.setThreadPriority(Process.THREAD_PRIORITY_BACKGROUND);
        try{
            File dir=new File(getNoBackupFilesDir(),"plantbrush-v1");if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Cannot create AI storage");
            JSONObject manifest=new JSONObject(new String(read(getAssets().open("plantbrush/manifest.json"),16384),StandardCharsets.UTF_8));
            JSONObject files=manifest.getJSONObject("files");
            android.content.SharedPreferences receipts=getSharedPreferences("verified-plantbrush-models",0);
            android.content.SharedPreferences.Editor verified=receipts.edit();
            for(Iterator<String> names=files.keys();names.hasNext();){
                String name=names.next();if(!name.matches("[A-Za-z0-9_.-]+"))throw new IOException("Invalid model filename");
                File target=new File(dir,name);String hash=files.getString(name),stamp=ModelStamp.of(name,target,hash);
                // Never scan the large model again when this exact private file
                // has already passed SHA-256 verification. Update/missing/changed
                // files take the full verify-and-replace path.
                if(stamp!=null&&stamp.equals(receipts.getString(name,null)))continue;
                ManagedFiles.replace(dir,target,hash,()->getAssets().open("plantbrush/"+name),
                    (from,to)->android.system.Os.rename(from.getAbsolutePath(),to.getAbsolutePath()));
                stamp=ModelStamp.of(name,target,hash);if(stamp!=null)verified.putString(name,stamp);
            }
            verified.apply();
            if(stopped)return;
            recognizer=new PlantbrushRecognizer(dir);
            // Loading a session is not proof that CPU inference is compatible.
            // Exercise the native kernels before accepting an Identify request.
            int[] warmup=new int[224*224];Arrays.fill(warmup,0xffffffff);
            recognizer.encode(new PlantbrushMath.Image(224,224,warmup));
            Log.i("PvZFPlantbrush","Native inference warmup passed");
            ServerSocket s=new ServerSocket();server=s;s.setReuseAddress(false);
            s.bind(new InetSocketAddress(InetAddress.getByName("127.0.0.1"),17861),2);
            s.setSoTimeout(1000);state=2;Log.i("PvZFPlantbrush","Offline recognition ready; loopback only; PID="+Process.myPid());
            while(!stopped){
                try(Socket client=s.accept()){requestStarted=SystemClock.elapsedRealtime();client.setSoTimeout(10000);handle(client);}
                catch(SocketTimeoutException idle){}
                catch(Exception bad){if(!stopped)Log.w("PvZFPlantbrush","Request failed",bad);}
                finally{requestStarted=0;}
            }
        }catch(Exception|LinkageError e){state=-1;Log.e("PvZFPlantbrush","AI unavailable; game process is unaffected",e);}
        finally{if(recognizer!=null)recognizer.close();try{if(server!=null)server.close();}catch(IOException ignored){}}
    }
    private void handle(Socket socket)throws Exception{
        InputStream input=new BufferedInputStream(socket.getInputStream());
        String request=line(input);String[] parts=request.split(" ");
        if(parts.length!=3){reply(socket,400,error("Invalid request"));return;}
        Map<String,String> headers=new HashMap<>();int bytes=request.length();
        for(int i=0;i<40;i++){
            String h=line(input);bytes+=h.length();if(bytes>8192)throw new IOException("Headers too long");if(h.isEmpty())break;
            int colon=h.indexOf(':');if(colon<1)throw new IOException("Bad header");
            String key=h.substring(0,colon).toLowerCase(Locale.ROOT);if(headers.put(key,h.substring(colon+1).trim())!=null)throw new IOException("Duplicate header");
            if(i==39)throw new IOException("Too many headers");
        }
        if(parts[0].equals("GET")&&parts[1].equals("/health")){
            reply(socket,200,new JSONObject().put("success",true).put("service","MaLiangLocalRecognizer").put("protocol_version",1)
                .put("recognition_revision",3).put("plant_count",718).put("prototype",true));return;
        }
        if(!parts[0].equals("POST")||!parts[1].equals("/recognize")){reply(socket,404,error("Unknown endpoint"));return;}
        if(headers.containsKey("transfer-encoding")){reply(socket,400,error("Chunked input is not supported"));return;}
        int length;try{length=Integer.parseInt(headers.get("content-length"));}catch(Exception e){length=0;}
        if(length<1||length>4194304){reply(socket,413,error("Drawing must be between 1 byte and 4 MiB"));return;}
        byte[] png=new byte[length];new DataInputStream(input).readFully(png);
        BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;
        BitmapFactory.decodeByteArray(png,0,png.length,bounds);
        if(bounds.outWidth<1||bounds.outHeight<1||bounds.outWidth>4096||bounds.outHeight>4096){reply(socket,400,error("Invalid drawing dimensions"));return;}
        Integer target=null;
        if(headers.containsKey("x-maliang-plant-type"))try{target=Integer.valueOf(headers.get("x-maliang-plant-type"));}catch(NumberFormatException e){reply(socket,400,error("Invalid target plant"));return;}
        Bitmap bitmap=BitmapFactory.decodeByteArray(png,0,png.length);
        if(bitmap==null){reply(socket,400,error("Drawing could not be decoded"));return;}
        int width=bitmap.getWidth(),height=bitmap.getHeight();int[] pixels=new int[width*height];bitmap.getPixels(pixels,0,width,0,0,width,height);bitmap.recycle();
        long start=SystemClock.elapsedRealtime();
        try{JSONObject result=recognizer.recognize(new PlantbrushMath.Image(width,height,pixels),target);reply(socket,200,result);
            Log.i("PvZFPlantbrush","Recognize ms="+(SystemClock.elapsedRealtime()-start)+" plant="+result.optInt("plantType",-1)+" similarity="+result.optDouble("similarity",0));}
        catch(Exception e){Log.e("PvZFPlantbrush","Inference failed",e);reply(socket,500,error("Recognition failed. Please try again."));}
    }
    private static JSONObject error(String message)throws JSONException{return new JSONObject().put("success",false).put("recognized",false).put("message",message);}
    private static String line(InputStream in)throws IOException{
        ByteArrayOutputStream out=new ByteArrayOutputStream();int c;
        while((c=in.read())!=-1&&c!=10){if(out.size()>=2048)throw new IOException("Line too long");if(c!=13)out.write(c);}
        if(c==-1)throw new EOFException();return out.toString("US-ASCII");
    }
    private static byte[] read(InputStream in,int limit)throws IOException{
        try(InputStream stream=in;ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[4096];int n;while((n=stream.read(b))!=-1){if(out.size()+n>limit)throw new IOException("Asset too large");out.write(b,0,n);}return out.toByteArray();
        }
    }
    private static void reply(Socket socket,int status,JSONObject data)throws IOException{
        byte[] body=data.toString().getBytes(StandardCharsets.UTF_8);
        OutputStream out=socket.getOutputStream();out.write(("HTTP/1.1 "+status+" Result\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: "+body.length+"\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII));out.write(body);out.flush();
    }
    public void onDestroy(){
        stopped=true;state=0;try{if(server!=null)server.close();}catch(IOException ignored){}
        // This component is declared in :plantbrush, never the game's process.
        // Unbinding releases the entire native allocator even if an inference is stuck.
        super.onDestroy();Process.killProcess(Process.myPid());
    }
}
