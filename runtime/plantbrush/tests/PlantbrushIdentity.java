import com.android.tools.smali.dexlib2.*;
import com.android.tools.smali.dexlib2.iface.*;
import com.android.tools.smali.dexlib2.iface.value.*;
import com.android.tools.smali.dexlib2.immutable.value.*;
import com.android.tools.smali.dexlib2.rewriter.*;
import com.android.tools.smali.dexlib2.writer.pool.DexPool;
import java.io.File;
public final class PlantbrushIdentity {
 public static void main(String[] args)throws Exception {
  String old="com.LanPiaoPiao.PlantsVsZombiesEN",next=old+"AI";
  DexFile dex=DexFileFactory.loadDexFile(new File(args[0]),Opcodes.getDefault());int hits=0;
  for(ClassDef c:dex.getClasses())for(Field f:c.getFields())if(f.getInitialValue() instanceof StringEncodedValue && ((StringEncodedValue)f.getInitialValue()).getValue().equals(old)) {
   if(!c.getType().endsWith("/BuildConfig;")||!f.getName().equals("APPLICATION_ID"))throw new AssertionError("Unexpected identity field");hits++;
  }
  if(hits!=1)throw new AssertionError("Expected exactly one BuildConfig identity");
  DexRewriter rewrite=new DexRewriter(new RewriterModule(){
   public Rewriter<EncodedValue> getEncodedValueRewriter(Rewriters rs){return new EncodedValueRewriter(rs){
    public EncodedValue rewrite(EncodedValue v){if(v instanceof StringEncodedValue && ((StringEncodedValue)v).getValue().equals(old))return new ImmutableStringEncodedValue(next);return super.rewrite(v);}
   };}
  });
  DexPool.writeTo(args[1],rewrite.getDexFileRewriter().rewrite(dex));
  DexFile check=DexFileFactory.loadDexFile(new File(args[1]),Opcodes.getDefault());
  if(check.getClasses().size()!=dex.getClasses().size())throw new AssertionError("Classes changed");
  System.out.println("Rebuilt DEX: one BuildConfig APPLICATION_ID; "+check.getClasses().size()+" classes");
 }
}
