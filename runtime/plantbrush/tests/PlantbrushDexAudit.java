import com.android.tools.smali.dexlib2.*;
import com.android.tools.smali.baksmali.*;
import java.io.File;
public final class PlantbrushDexAudit {
 public static void main(String[] args)throws Exception{
  if(!Baksmali.disassembleDexFile(DexFileFactory.loadDexFile(new File(args[0]),Opcodes.getDefault()),new File(args[1]),2,new BaksmaliOptions()))throw new AssertionError("DEX disassembly failed");
 }
}
