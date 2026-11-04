package com.silvershadow.pvzf;
import java.nio.*;
import java.util.*;
import java.io.*;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;

public final class PlantbrushOptimizationTest {
 public static void main(String[] args)throws Exception{
  Random random=new Random(41);int checks=0;
  for(int round=0;round<160;round++){
   int n=round<8?round:5952;float[] scores=new float[n];Integer[] expected=new Integer[n];
   for(int i=0;i<n;i++){scores[i]=round%2==0?random.nextInt(9):random.nextFloat();expected[i]=i;}
   if(n>5){scores[0]=Float.NaN;scores[1]=-0f;scores[2]=0f;}
   Arrays.sort(expected,(a,b)->Float.compare(scores[b],scores[a]));int[] order=new int[n],scratch=new int[n];PlantbrushMath.rank(scores,order,scratch);
   for(int i=0;i<n;i++)if(order[i]!=expected[i])throw new AssertionError("Ranking/tie behavior changed");checks++;
  }
  for(String name:new String[]{"blank","rectangle","pea","pea-target","wallnut","starfruit"}){
   BufferedImage image=ImageIO.read(new File(args[0],name+".png"));int[] pixels=image.getRGB(0,0,image.getWidth(),image.getHeight(),null,0,image.getWidth());
   PlantbrushMath.Image normal=PlantbrushMath.normal(new PlantbrushMath.Image(image.getWidth(),image.getHeight(),pixels.clone()));
   BaselinePlantbrushMath.Image old=BaselinePlantbrushMath.normal(new BaselinePlantbrushMath.Image(image.getWidth(),image.getHeight(),pixels.clone()));
   if(!Arrays.equals(PlantbrushMath.shape(normal),BaselinePlantbrushMath.shape(old)))throw new AssertionError("Shape changed: "+name);
   FloatBuffer direct=ByteBuffer.allocateDirect(3*224*224*4).order(ByteOrder.nativeOrder()).asFloatBuffer();PlantbrushMath.tensor(normal,direct);
   float[] expected=BaselinePlantbrushMath.tensor(old);for(float v:expected)if(Float.floatToIntBits(v)!=Float.floatToIntBits(direct.get()))throw new AssertionError("Tensor changed");
   checks+=2;
  }
  System.out.println(checks+" ranking and exact preprocessing checks passed");
 }
}
