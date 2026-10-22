package com.silvershadow.pvzf;
import java.io.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.nio.file.*;
import org.json.*;
public final class PlantbrushHostTest {
    public static void main(String[] args)throws Exception{
        File assets=new File(args[0]),fixtures=new File(args[1]);
        JSONObject expected=new JSONObject(Files.readString(new File(fixtures,"upstream-results.json").toPath()));
        JSONObject report=new JSONObject();
        final String[] current={""};
        try(PlantbrushRecognizer recognizer=new PlantbrushRecognizer(assets,tensor->{
            float[] values=new float[512];try(DataInputStream in=new DataInputStream(new FileInputStream(new File(fixtures,current[0]+"-java-embedding.bin")))){for(int i=0;i<512;i++)values[i]=in.readFloat();}return values;
        })){
            for(String name:new String[]{"blank","rectangle","pea","pea-target","wallnut","starfruit"}){
                BufferedImage image=ImageIO.read(new File(fixtures,name+".png"));
                PlantbrushMath.Image input=new PlantbrushMath.Image(image.getWidth(),image.getHeight(),image.getRGB(0,0,image.getWidth(),image.getHeight(),null,0,image.getWidth()));
                current[0]=name;
                if(args.length>2&&args[2].equals("preprocess")){
                    try(DataOutputStream out=new DataOutputStream(new FileOutputStream(new File(fixtures,name+"-java-tensor.bin")))){for(float v:PlantbrushMath.tensor(PlantbrushMath.normal(input)))out.writeFloat(v);}
                    continue;
                }
                Integer target=name.equals("pea-target")?0:null;
                JSONObject actual=recognizer.recognize(input,target),reference=expected.getJSONObject(name).getJSONObject("result");
                if(actual.getBoolean("recognized")!=reference.getBoolean("recognized"))throw new AssertionError(name+" rejection changed: "+actual);
                if(actual.getInt("plantType")!=reference.getInt("plantType"))throw new AssertionError(name+" top plant changed: "+actual);
                if(Math.abs(actual.optDouble("similarity",0)-reference.optDouble("similarity",0))>.025)throw new AssertionError(name+" score changed");
                float[] embedding=recognizer.encode(PlantbrushMath.normal(input));double dot=0,norm=0;
                try(DataInputStream in=new DataInputStream(new FileInputStream(new File(fixtures,name+"-embedding.bin")))){
                    for(float v:embedding){float ref=in.readFloat();dot+=v*ref;norm+=ref*ref;}
                }
                double cosine=dot/Math.sqrt(norm);if(cosine<.999)throw new AssertionError(name+" preprocessing drift "+cosine);
                report.put(name,new JSONObject().put("embedding_cosine",cosine).put("result",actual));
                System.out.println(name+" passed; top="+actual.getInt("plantType")+" cosine="+cosine);
            }
        }
        Files.writeString(new File(fixtures,"java-results.json").toPath(),report.toString(2));
    }
}
