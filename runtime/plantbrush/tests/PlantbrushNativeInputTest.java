package com.silvershadow.pvzf;
import java.io.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;

/** Exercise the reused direct tensor with real CPU inference, changing inputs. */
public final class PlantbrushNativeInputTest {
 public static void main(String[] args)throws Exception{
  try(PlantbrushRecognizer recognizer=new PlantbrushRecognizer(new File(args[0]))){
   for(int pass=0;pass<2;pass++)for(String name:new String[]{"pea","wallnut","starfruit"}){
    BufferedImage im=ImageIO.read(new File(args[1],name+".png"));
    PlantbrushMath.Image input=new PlantbrushMath.Image(im.getWidth(),im.getHeight(),im.getRGB(0,0,im.getWidth(),im.getHeight(),null,0,im.getWidth()));
    float[] actual=recognizer.encode(PlantbrushMath.normal(input));double dot=0,norm=0;
    try(DataInputStream in=new DataInputStream(new FileInputStream(new File(args[1],name+"-embedding.bin")))){
     for(float v:actual){float reference=in.readFloat();dot+=v*reference;norm+=reference*reference;}
    }
    double cosine=dot/Math.sqrt(norm);if(cosine<.999)throw new AssertionError("Reused input drift: "+name+" "+cosine);
    System.out.println(name+" pass "+pass+" actual CPU embedding cosine "+cosine);
   }
  }
 }
}
