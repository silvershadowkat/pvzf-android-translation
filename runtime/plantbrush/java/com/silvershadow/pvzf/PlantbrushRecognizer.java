package com.silvershadow.pvzf;

import ai.onnxruntime.*;
import java.io.*;
import java.nio.FloatBuffer;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import org.json.*;

/** Revision-3 matching against the supplied 718-plant index. CPU only, two threads. */
public final class PlantbrushRecognizer implements AutoCloseable {
    private final OrtEnvironment environment;
    private final OrtSession session;
    private final FloatBuffer inputBuffer;
    private final OnnxTensor inputTensor;
    private final Map<String,OnnxTensor> inputs;
    private final int[] order=new int[5952],sortScratch=new int[5952];
    private final JSONArray catalog;
    private final float[][] features,negative,shapes,spatial,variantColors,negativeShapes;
    private final int[] records;
    private final Map<String,List<Integer>> aliases=new LinkedHashMap<>();
    private final Set<Integer> plantTypes=new HashSet<>();
    interface Encoder {float[] encode(float[] tensor)throws Exception;}
    private final Encoder testEncoder;
    public PlantbrushRecognizer(File dir)throws Exception{
        this(dir,null);
    }
    PlantbrushRecognizer(File dir,Encoder encoder)throws Exception{
        testEncoder=encoder;
        catalog=new JSONArray(new String(Files.readAllBytes(new File(dir,"catalog.json").toPath()),StandardCharsets.UTF_8));
        if(catalog.length()!=744)throw new IOException("Unexpected reference catalog");
        try(DataInputStream in=new DataInputStream(new BufferedInputStream(new FileInputStream(new File(dir,"index.bin"))))){
            byte[] magic=new byte[8];in.readFully(magic);if(!Arrays.equals(magic,"PVZAI001".getBytes(StandardCharsets.US_ASCII)))throw new IOException("Invalid index");
            features=matrix(in,5952,512);
            if(in.readInt()!=5952||in.readInt()!=1)throw new IOException("Invalid records");
            records=new int[5952];for(int i=0;i<records.length;i++){records[i]=in.readInt();if(records[i]<0||records[i]>=744)throw new IOException("Invalid reference");}
            negative=matrix(in,256,512);matrix(in,744,16);shapes=matrix(in,744,1024);spatial=matrix(in,744,1728);
            variantColors=matrix(in,5952,16);negativeShapes=matrix(in,256,1024);if(in.read()!=-1)throw new IOException("Trailing index data");
        }
        for(int i=0;i<catalog.length();i++){
            aliases.computeIfAbsent(catalog.getJSONObject(i).getString("fingerprint"),k->new ArrayList<>()).add(i);
            plantTypes.add(catalog.getJSONObject(i).getInt("plantType"));
        }
        if(encoder!=null){environment=null;session=null;inputBuffer=null;inputTensor=null;inputs=null;return;}
        environment=OrtEnvironment.getEnvironment();
        try(OrtSession.SessionOptions options=new OrtSession.SessionOptions()){
            options.setIntraOpNumThreads(2);options.setInterOpNumThreads(1);
            options.addConfigEntry("session.intra_op.allow_spinning","0");
            options.addConfigEntry("session.inter_op.allow_spinning","0");
            options.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT);
            session=environment.createSession(new File(dir,"vision.onnx").getAbsolutePath(),options);
        }
        try{
            inputBuffer=ByteBuffer.allocateDirect(3*224*224*4).order(ByteOrder.nativeOrder()).asFloatBuffer();
            inputTensor=OnnxTensor.createTensor(environment,inputBuffer,new long[]{1,3,224,224});
            inputs=Collections.singletonMap("image",inputTensor);
        }catch(Exception|Error failure){session.close();throw failure;}
    }
    private static float[][] matrix(DataInputStream in,int rows,int cols)throws IOException{
        if(in.readInt()!=rows||in.readInt()!=cols)throw new IOException("Unexpected index dimensions");
        float[][] data=new float[rows][cols];for(int r=0;r<rows;r++)for(int c=0;c<cols;c++){data[r][c]=in.readFloat();if(!Float.isFinite(data[r][c]))throw new IOException("Non-finite index");}return data;
    }
    public float[] encode(PlantbrushMath.Image normal)throws Exception{
        if(testEncoder!=null)return testEncoder.encode(PlantbrushMath.tensor(normal));
        PlantbrushMath.tensor(normal,inputBuffer);
        try(OrtSession.Result result=session.run(inputs)){
            float[] embedding=((float[][])result.get(0).getValue())[0];double norm=0;
            for(float f:embedding)norm+=f*f;norm=Math.sqrt(norm);
            if(norm<1e-9||!Double.isFinite(norm))throw new IOException("Invalid model output");
            for(int i=0;i<embedding.length;i++)embedding[i]/=norm;return embedding;
        }
    }
    private static float[] dots(float[][] matrix,float[] query){float[] r=new float[matrix.length];for(int i=0;i<r.length;i++)for(int j=0;j<query.length;j++)r[i]+=matrix[i][j]*query[j];return r;}
    private static float max(float[] a){float m=-Float.MAX_VALUE;for(float v:a)m=Math.max(m,v);return m;}
    private static JSONObject reject(JSONObject result,String message,String reason)throws JSONException{return result.put("message",message).put("rejectionReason",reason);}
    boolean supportsTarget(Integer target){return target==null||plantTypes.contains(target);}
    public JSONObject recognize(PlantbrushMath.Image image,Integer target)throws Exception{
        if(image.w>4096||image.h>4096)throw new IOException("Drawing too large");
        if(!supportsTarget(target))throw new IOException("Unknown target plant");
        JSONObject appearance=PlantbrushMath.appearance(image);
        JSONObject result=new JSONObject().put("success",true).put("recognized",false).put("plantType",-1).put("candidates",new JSONArray())
            .put("strength",0).put("needsConfirmation",false).put("appearance",appearance).put("model","CLIP ViT-B/32, Android local prototype").put("recognitionRevision",3);
        if(target!=null)result.put("targetPlantType",target);
        if(!appearance.getBoolean("valid"))return result.put("message",appearance.getString("message"));
        PlantbrushMath.Image normal=PlantbrushMath.normal(image);
        if(target==null&&PlantbrushMath.primitive(normal))return reject(result,"Add the plant's body and inner features, not just a geometric outline.","simple_geometry");
        float[] embedding=encode(normal),scores=dots(features,embedding),negScores=dots(negative,embedding);
        float positive=max(scores),negativeScore=max(negScores),margin=positive-negativeScore;
        JSONObject evidence=new JSONObject().put("plantSimilarity",PlantbrushMath.rounded(positive,5)).put("nonPlantSimilarity",PlantbrushMath.rounded(negativeScore,5)).put("margin",PlantbrushMath.rounded(margin,5));result.put("evidence",evidence);
        float[] shape=PlantbrushMath.shape(normal),shapeScores=PlantbrushMath.agreement(shape,shapes,32,1,3);
        float filledFraction=PlantbrushMath.ink(normal)/Math.max(.01f,PlantbrushMath.mean(shape));boolean support=false;
        if(margin>=-.015&&margin<.003){
            float[] negShape=PlantbrushMath.agreement(shape,negativeShapes,32,1,3);float positiveJoint=-1,negativeJoint=-1;
            for(int i=0;i<scores.length;i++)positiveJoint=Math.max(positiveJoint,.65f*scores[i]+.35f*shapeScores[records[i]]);
            for(int i=0;i<negScores.length;i++)negativeJoint=Math.max(negativeJoint,.65f*negScores[i]+.35f*negShape[i]);
            float structureMargin=positiveJoint-negativeJoint;support=structureMargin>=.018&&filledFraction<.4;
            evidence.put("structureMargin",PlantbrushMath.rounded(structureMargin,5)).put("inkFillRatio",PlantbrushMath.rounded(filledFraction,5));
        }
        if(target==null&&(positive<.72||margin<.003&&!support))return reject(result,"Add clearer plant features, then try again.","non_plant_or_insufficient_evidence");
        for(int i=0;i<744;i++)scores[i*8+3]=.5f*scores[i*8]+.5f*scores[i*8+3];
        float[] spatialScores=PlantbrushMath.agreement(PlantbrushMath.spatial(normal),spatial,24,3,1),colors=PlantbrushMath.colors(normal);
        float shapeWeight=positive>=.9?.5f:.35f,spatialWeight=filledFraction>.55?(positive>=.9?.3f:.15f):0;
        for(int i=0;i<scores.length;i++)scores[i]=(1-shapeWeight-spatialWeight)*scores[i]+shapeWeight*shapeScores[records[i]]+spatialWeight*spatialScores[records[i]];
        for(int offset:new int[]{0,8}){
            float norm=0;for(int j=0;j<8;j++)norm+=colors[offset+j]*colors[offset+j];if(Math.sqrt(norm)<=.1)continue;
            for(int i=0;i<scores.length;i++){float agreement=0;for(int j=0;j<8;j++)agreement+=variantColors[i][offset+j]*colors[offset+j];scores[i]-=(offset==0?.3f:.08f)*(1-agreement);}
        }
        for(List<Integer> group:aliases.values())if(group.size()>1){float best=-1;for(int ref:group)for(int j=0;j<8;j++)best=Math.max(best,scores[ref*8+j]);for(int ref:group)for(int j=0;j<8;j++)scores[ref*8+j]=best;}
        PlantbrushMath.rank(scores,order,sortScratch);
        LinkedHashMap<Integer,JSONObject> best=new LinkedHashMap<>();
        for(int index:order){
            JSONObject ref=catalog.getJSONObject(records[index]);int plant=ref.getInt("plantType");if(best.containsKey(plant))continue;
            JSONObject candidate=new JSONObject().put("plantType",plant).put("enumName",ref.getString("enumName")).put("displayName",ref.getString("displayName"))
                .put("similarity",PlantbrushMath.rounded(scores[index],5)).put("skinIndex",ref.getInt("skinIndex"));
            best.put(plant,candidate);if(best.size()>=5&&(target==null||best.containsKey(target)))break;
        }
        JSONArray candidates=new JSONArray();for(JSONObject c:best.values()){if(candidates.length()==5)break;candidates.put(c);}
        JSONObject first=target==null?candidates.getJSONObject(0):best.get(target);
        double gap=candidates.length()>1?first.getDouble("similarity")-candidates.getJSONObject(1).getDouble("similarity"):0;
        boolean uncertain=first.getDouble("similarity")<.78||gap<.04;
        TreeSet<Integer> ambiguous=new TreeSet<>();
        for(int i=0;i<catalog.length();i++)if(catalog.getJSONObject(i).getInt("plantType")==first.getInt("plantType")){
            for(int ref:aliases.get(catalog.getJSONObject(i).getString("fingerprint")))ambiguous.add(catalog.getJSONObject(ref).getInt("plantType"));break;
        }
        if(ambiguous.size()>1){uncertain=true;result.put("ambiguousPlantTypes",new JSONArray(ambiguous));}
        for(String key:new String[]{"plantType","enumName","displayName","similarity"})result.put(key,first.get(key));
        return result.put("recognized",true).put("needsConfirmation",target==null&&uncertain).put("strength",appearance.getDouble("strength")).put("candidates",candidates)
            .put("message",target!=null?"Calculated similarity and strength for the selected plant.":ambiguous.size()>1?"These plants share the same appearance. Please choose the intended plant.":uncertain?"Choose the plant that best matches your drawing.":"Found the closest plant.");
    }
    public void close(){if(inputTensor!=null)inputTensor.close();try{if(session!=null)session.close();}catch(OrtException ignored){}}
}
