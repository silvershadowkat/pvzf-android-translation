package com.silvershadow.pvzf;

/** Once per game process; never starts Unity in the optional AI service. */
public final class ProcessStartGate {
    public interface Prepare { void run() throws Exception; }
    private boolean ready;
    public synchronized boolean ensure(String applicationId,String processName,Prepare prepare) throws Exception {
        if(applicationId==null||processName==null||processName.isEmpty())
            throw new IllegalStateException("Cannot identify game process");
        if(!applicationId.equals(processName))return false;
        if(!ready){prepare.run();ready=true;}
        return true;
    }
}
