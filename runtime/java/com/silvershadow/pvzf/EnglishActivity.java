package com.silvershadow.pvzf;

import android.os.Bundle;
import android.app.AlertDialog;
import android.system.Os;
import android.util.Log;
import android.app.Activity;
import android.content.Intent;
import android.content.Context;
import org.json.*;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.regex.*;

/** Runs before Unity opens metadata. Never reads, modifies or deletes player saves. */
public final class EnglishActivity extends Activity {
    private static Context context;
    private static final String TAG = "PvZFEnglish";
    private static final String METADATA = "assets/bin/Data/Managed/Metadata/global-metadata.dat";
    private static final Map<String,String> exact = new HashMap<>();
    private static final Map<String,String[]> onlineLevels = new HashMap<>();
    private static final Map<String,String> levelDisplays = new HashMap<>();
    private static final Set<String> ambiguousLevelDisplays = new HashSet<>();
    private static final List<Rule> rules = new ArrayList<>();
    private static final Set<String> recipeNames = new HashSet<>();
    // Recursive line/tag translation benefits from a Java cache too. Bound its
    // retained text bytes as well as entry count, including negative matches.
    private static final BoundedTextCache cache = new BoundedTextCache(1024,1024*1024);
    private static final Pattern SLOT = Pattern.compile("\\{(\\d+)\\}");
    private static final Pattern MARKUP = Pattern.compile("</?(?:color|size|b|i|u|s|nobr|align|voffset|font|mark|alpha|cspace|mspace|indent|line-height)(?:=[^<>]*)?>",Pattern.CASE_INSENSITIVE);
    private static final class Rule {
        final Pattern pattern; final String replacement,prefix; final boolean recipe;
        Rule(String p,String r) {pattern=Pattern.compile(p);replacement=r;prefix=RegexPrefix.of(p);
            recipe=r.startsWith("You haven't discovered this plant yet!");}
    }
    private static native void startRuntime(boolean blooms);

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        context=getApplicationContext();
        // Keep the handoff to Unity's launch logo free of internal status text.
        android.view.View background=new android.view.View(this);
        background.setBackgroundColor(android.graphics.Color.BLACK);
        setContentView(background);
        new Thread(()->prepareAndLaunch(),"EnglishFileRefresh").start();
    }

    private void prepareAndLaunch() {
        try {
            prepareManagedFiles();
            loadTranslations();
            // Load only; Unity remains responsible for calling il2cpp_init.
            // Install the completion hook before starting Unity's Activity.
            System.loadLibrary("il2cpp");
            System.loadLibrary("pvzfenglish");
            startRuntime(getSharedPreferences("english-runtime",0).getBoolean("blooms",true));
        } catch (Exception | LinkageError e) {
            // Do not open Unity with an override that failed verification.
            Log.e(TAG,"English startup failed",e);
            runOnUiThread(()->new AlertDialog.Builder(this).setTitle("English update could not finish")
                .setMessage("Your saves have not been removed. Close the game, free some storage if needed, and try again.")
                .setCancelable(false).setPositiveButton("Close",(d,w)->finish()).show());
            return;
        }
        runOnUiThread(()->{
            Intent game=new Intent();game.setClassName(this,"com.unity3d.player.UnityPlayerActivity");
            startActivity(game);finish();
        });
    }


    private byte[] asset(String name) throws IOException {
        try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toByteArray();
        }
    }
    private void replace(String asset,File target,String expected) throws Exception {
        File external=getExternalFilesDir(null);
        File root=external!=null && target.getAbsolutePath().startsWith(external.getAbsolutePath()+File.separator)?external:getFilesDir();
        ManagedFiles.replace(root,target,expected,()->getAssets().open(asset),
            (from,to)->Os.rename(from.getAbsolutePath(),to.getAbsolutePath()));
    }
    private void prepareManagedFiles() throws Exception {
        JSONObject manifest=new JSONObject(new String(asset("english/manifest.json"),"UTF-8"));
        String expected=manifest.getString("metadata_sha256");
        // Exact, known metadata override only. Every save slot and unknown file stays untouched.
        File external=getExternalFilesDir(null);
        if(external==null)throw new IOException("Game storage unavailable");
        for(File root:new File[]{external,getFilesDir()}) {
            File target=new File(root,"il2cpp/Metadata/global-metadata.dat");
            if(target.exists() || (root.equals(external) && manifest.optBoolean("refresh_test_seed",false)))
                replace(METADATA.substring(7),target,expected);
        }
        JSONObject almanacs=manifest.getJSONObject("almanac_files");
        java.util.Map<String,String> almanacHashes=new java.util.HashMap<>();
        Iterator<String> almanacNames=almanacs.keys();
        while(almanacNames.hasNext()){String name=almanacNames.next();almanacHashes.put(name,almanacs.getString(name));}
        for(File root:new File[]{external,getFilesDir()})
            ManagedFiles.refreshAlmanacs(root,almanacHashes,name->getAssets().open("english-almanac/"+name),
                (from,to)->Os.rename(from.getAbsolutePath(),to.getAbsolutePath()),
                root.equals(external) && manifest.optBoolean("refresh_test_seed",false));
        JSONObject files=manifest.getJSONObject("files");
        android.content.SharedPreferences prefs=getSharedPreferences("english-runtime",0);
        Iterator<String> names=files.keys();
        while(names.hasNext()) {
            String name=names.next();
            if(!name.matches("[A-Za-z0-9_.-]+"))throw new IOException("Invalid managed filename");
            // The translator reads this dictionary directly from the APK below.
            // Its old private copy is never consulted; do not re-copy/hash it.
            if(name.equals("translations.json"))continue;
            File target=new File(getFilesDir(),"english-runtime/"+name);
            // Music is embedded as Unity AudioClips in 4.1. Only small
            // managed support assets remain; no audio extraction or receipts.
            replace("english/"+name,target,files.getString(name));
        }
        if(!prefs.edit().putString("revision",manifest.getString("revision")).commit())
            throw new IOException("Cannot record completed refresh");
        Log.i(TAG,"Managed files verified; player data untouched; revision="+manifest.getString("revision"));
    }
    private static boolean translationsLoaded;
    private void loadTranslations() throws Exception {
        synchronized(EnglishActivity.class) {
        if(translationsLoaded)return;
        JSONObject data=new JSONObject(new String(asset("english/translations.json"),"UTF-8"));
        JSONObject pairs=data.getJSONObject("exact");Iterator<String> keys=pairs.keys();
        while(keys.hasNext()){String k=keys.next();exact.put(k,pairs.getString(k));}
        JSONArray ingredients=data.optJSONArray("recipe_names");
        if(ingredients!=null)for(int i=0;i<ingredients.length();i++)recipeNames.add(ingredients.getString(i));
        JSONArray rs=data.getJSONArray("regex");
        for(int i=0;i<rs.length();i++) {JSONArray r=rs.getJSONArray(i);rules.add(new Rule(r.getString(0),r.getString(1)));}
        JSONObject levels=data.optJSONObject("online_levels");
        if(levels!=null){Iterator<String> ids=levels.keys();while(ids.hasNext()){
            String id=ids.next();JSONObject row=levels.getJSONObject(id);
            if(id.matches("level_[0-9]+_[A-Za-z0-9]+"))onlineLevels.put(id,new String[]{row.getString("name"),row.getString("startTip")});
        }}
        for(String[] pair:PlantbrushTranslations.EXACT)if(!exact.containsKey(pair[0]))exact.put(pair[0],pair[1]);
        for(String[] rule:PlantbrushTranslations.RULES)rules.add(new Rule(rule[0],rule[1]));
        Log.i(TAG,"Display translations loaded: "+exact.size()+" exact, "+rules.size()+" regex");
        translationsLoaded=true;
        }
    }
    public static synchronized String translate(String text) {
        if(text==null||text.length()>16384)return text;
        boolean cjk=false;for(int i=0;i<text.length();i++){char c=text.charAt(i);if(c>=0x3400&&c<=0x9fff){cjk=true;break;}}
        if(!cjk)return text;
        String result=cache.get(text);if(result!=null)return result;
        result=levelDisplays.get(text);if(result==null)result=exact.get(text);
        if(result==null) {
            String trimmed=text.trim();result=exact.get(trimmed);
            if(result!=null)result=text.substring(0,text.indexOf(trimmed))+result+text.substring(text.indexOf(trimmed)+trimmed.length());
        }
        if(result==null)for(Rule rule:rules) {
            if(!text.startsWith(rule.prefix))continue;
            Matcher m=rule.pattern.matcher(text);
            // Complete display match only; never rewrite a partial gameplay identifier.
            if(!m.matches())continue;
            // This recipe rule describes named fusion ingredients. A global
            // '+' rule also matched research counters and modifier bonuses.
            if(rule.recipe&&(m.groupCount()!=2||!recipeNames.contains(m.group(1).trim())||!recipeNames.contains(m.group(2).trim())))continue;
            Matcher slots=SLOT.matcher(rule.replacement);StringBuffer b=new StringBuffer();boolean valid=true;
            while(slots.find()) {
                int n=Integer.parseInt(slots.group(1))+1;if(n>m.groupCount()){valid=false;break;}
                String value=m.group(n);String translated=exact.get(value);
                slots.appendReplacement(b,Matcher.quoteReplacement(translated!=null?translated:(value==null?"":value)));
            }
            if(valid){slots.appendTail(b);result=b.toString();break;}
        }
        // Almanac panels combine translated headings with Chinese effect lines.
        // Apply the same complete-match policy to each line, retaining line endings.
        if(result==null && text.indexOf('\n')>=0) {
            StringBuilder lines=new StringBuilder();int start=0;
            while(start<text.length()) {
                int end=text.indexOf('\n',start);if(end<0)end=text.length();
                int contentEnd=end;if(contentEnd>start && text.charAt(contentEnd-1)=='\r')contentEnd--;
                lines.append(translate(text.substring(start,contentEnd)));
                lines.append(text,contentEnd,end);if(end<text.length())lines.append('\n');
                start=end+1;
            }
            result=lines.toString();
        }
        // PC translates styled text segments separately. Preserve every tag
        // verbatim and translate only complete text spans between recognized TMP
        // tags. Never strip tags or do unrestricted substring replacements.
        if(result==null || result.equals(text)) {
            Matcher tags=MARKUP.matcher(text);
            StringBuilder styled=new StringBuilder();int start=0;boolean found=false;
            while(tags.find()) {
                found=true;styled.append(translate(text.substring(start,tags.start())));
                styled.append(tags.group());start=tags.end();
            }
            if(found){styled.append(translate(text.substring(start)));result=styled.toString();}
        }
        if(result==null)result=text;
        cache.put(text,result);return result;
    }
    public static void saveMusic(boolean blooms) {
        if(context!=null)context.getSharedPreferences("english-runtime",0).edit().putBoolean("blooms",blooms).apply();
    }
    public static synchronized String onlineTitle(String id,String original) {
        String[] row=onlineLevels.get(id);return row==null||row[0].isEmpty()?original:row[0];
    }
    private static void registerLevelDisplay(String source,String target) {
        if(source==null||source.isEmpty()||target==null||target.isEmpty()||source.length()>16384||levelDisplays.size()>=256||ambiguousLevelDisplays.contains(source))return;
        String previous=levelDisplays.get(source);
        if(target.equals(previous))return; // Reopening the same level does not invalidate every cached label.
        if(previous!=null&&!previous.equals(target)){levelDisplays.remove(source);ambiguousLevelDisplays.add(source);}
        else levelDisplays.put(source,target);
        // Clear combined styled/line results too; they can depend on this text.
        cache.clear();
    }
    public static synchronized void registerOnlineLevel(String id,String originalName,String originalTip) {
        String[] row=onlineLevels.get(id);if(row==null)return;
        registerLevelDisplay(originalName,row[0]);registerLevelDisplay(originalTip,row[1]);
    }
}
