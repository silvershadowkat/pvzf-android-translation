import com.silvershadow.pvzf.ProcessStartGate;
public final class ProcessStartGateTest {
    static int checks;
    static void check(boolean ok){if(!ok)throw new AssertionError();checks++;}
    public static void main(String[] args)throws Exception{
        String app="com.LanPiaoPiao.PlantsVsZombiesENAI";int[] calls={0};
        ProcessStartGate gate=new ProcessStartGate();
        check(!gate.ensure(app,app+":plantbrush",()->{throw new AssertionError("Unity loaded in AI service");}));
        check(gate.ensure(app,app,()->{calls[0]++;}));
        // Application entry followed by launcher handoff in the same process.
        check(gate.ensure(app,app,()->{throw new AssertionError("Duplicate preparation");}));
        check(calls[0]==1);
        // Android recreates Unity without the launcher, in a new process.
        ProcessStartGate restored=new ProcessStartGate();
        check(restored.ensure(app,app,()->{calls[0]++;}));check(calls[0]==2);
        ProcessStartGate failed=new ProcessStartGate();
        try{failed.ensure(app,app,()->{throw new java.io.IOException("Refresh failed");});throw new AssertionError();}
        catch(java.io.IOException expected){checks++;}
        check(failed.ensure(app,app,()->{calls[0]++;}));check(calls[0]==3);
        try{gate.ensure(app,null,()->{throw new AssertionError();});throw new AssertionError();}
        catch(IllegalStateException expected){checks++;}
        System.out.println(checks+" process startup checks passed");
    }
}
