package com.silvershadow.pvzf;
import java.util.*;

/** Access-ordered text cache. The caller serializes access on the translator lock. */
public final class BoundedTextCache extends LinkedHashMap<String,String> {
    private final int entriesLimit,bytesLimit;
    private int bytes;
    public BoundedTextCache(int entries,int limit){super(256,.75f,true);entriesLimit=entries;bytesLimit=limit;}
    private static int cost(String key,String value){return 2*(key.length()+value.length());}
    public int retainedTextBytes(){return bytes;}
    @Override public String put(String key,String value){
        String old=remove(key);int size=cost(key,value);
        if(size>bytesLimit || entriesLimit<=0)return old;
        Iterator<Map.Entry<String,String>> it=entrySet().iterator();
        while(it.hasNext()&&(size()+1>entriesLimit||bytes+size>bytesLimit)){
            Map.Entry<String,String> e=it.next();bytes-=cost(e.getKey(),e.getValue());it.remove();
        }
        super.put(key,value);bytes+=size;return old;
    }
    @Override public String remove(Object key){String old=super.remove(key);if(old!=null)bytes-=cost((String)key,old);return old;}
    @Override public void clear(){super.clear();bytes=0;}
}
