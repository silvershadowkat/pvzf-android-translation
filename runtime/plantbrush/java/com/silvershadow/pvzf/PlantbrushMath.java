package com.silvershadow.pvzf;

import java.util.*;
import org.json.*;

/** Numeric port of revision-3 preprocessing and evidence rules. No Android UI APIs. */
public final class PlantbrushMath {
    static final int BOX=0,LINEAR=1,CUBIC=2;
    public static final class Image {
        final int w,h;final int[] rgb;
        public Image(int width,int height,int[] argb){
            w=width;h=height;rgb=argb;
            for(int i=0;i<rgb.length;i++){
                int p=rgb[i],a=p>>>24,r=(p>>>16)&255,g=(p>>>8)&255,b=p&255;
                rgb[i]=0xff000000|(((r*a+255*(255-a)+127)/255)<<16)|(((g*a+255*(255-a)+127)/255)<<8)|((b*a+255*(255-a)+127)/255);
            }
        }
        Image crop(int x,int y,int width,int height){int[] p=new int[width*height];for(int j=0;j<height;j++)System.arraycopy(rgb,(y+j)*w+x,p,j*width,width);return new Image(width,height,p);}
        Image resize(int width,int height,int filter){
            if(width==w&&height==h)return this;
            int[] horizontal=pass(rgb,w,h,width,filter,false);
            int[] vertical=pass(horizontal,width,h,height,filter,true);
            return new Image(width,height,vertical);
        }
    }
    static double kernel(double x,int filter){
        x=Math.abs(x);
        if(filter==BOX)return x<=.5?1:0;
        if(filter==LINEAR)return Math.max(0,1-x);
        if(x<1)return ((1.5*x-2.5)*x)*x+1;
        if(x<2)return ((-.5*x+2.5)*x-4)*x+2;
        return 0;
    }
    static int[] pass(int[] src,int w,int h,int size,int filter,boolean vertical){
        int old=vertical?h:w,other=vertical?w:h;
        if(old==size)return src;
        int[] dst=new int[size*other];double scale=(double)old/size,stretch=Math.max(1,scale),support=(filter==BOX?.5:filter==LINEAR?1:2)*stretch;
        for(int v=0;v<size;v++){
            double center=(v+.5)*scale;int lo=Math.max(0,(int)(center-support+.5)),hi=Math.min(old,(int)(center+support+.5));
            double[] weights=new double[hi-lo];double sum=0;
            for(int k=lo;k<hi;k++){double weight=kernel((k-center+.5)/stretch,filter);weights[k-lo]=weight;sum+=weight;}
            for(int t=0;t<other;t++){
                double r=0,g=0,b=0;
                for(int k=lo;k<hi;k++){int p=src[vertical?k*w+t:t*w+k];double z=weights[k-lo]/sum;r+=((p>>>16)&255)*z;g+=((p>>>8)&255)*z;b+=(p&255)*z;}
                dst[vertical?v*w+t:t*size+v]=0xff000000|(byteValue(r)<<16)|(byteValue(g)<<8)|byteValue(b);
            }
        }return dst;
    }
    static int byteValue(double d){return Math.max(0,Math.min(255,(int)Math.floor(d+.5)));}
    static int min(int p){return Math.min((p>>>16)&255,Math.min((p>>>8)&255,p&255));}
    static int max(int p){return Math.max((p>>>16)&255,Math.max((p>>>8)&255,p&255));}
    static Image normal(Image image){
        int x0=image.w,y0=image.h,x1=-1,y1=-1;
        for(int y=0;y<image.h;y++)for(int x=0;x<image.w;x++)if(min(image.rgb[y*image.w+x])<235){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}
        Image crop=x1>=0?image.crop(x0,y0,x1-x0+1,y1-y0+1):image;
        double scale=Math.min(1,190.0/Math.max(crop.w,crop.h));
        Image resized=crop.resize(Math.max(1,(int)Math.round(crop.w*scale)),Math.max(1,(int)Math.round(crop.h*scale)),CUBIC);
        int[] p=new int[224*224];Arrays.fill(p,-1);int left=(224-resized.w)/2,top=(224-resized.h)/2;
        for(int y=0;y<resized.h;y++)System.arraycopy(resized.rgb,y*resized.w,p,(y+top)*224+left,resized.w);
        return new Image(224,224,p);
    }
    static float[] tensor(Image normal){
        float[] out=new float[3*224*224],mean={.48145466f,.4578275f,.40821073f},sd={.26862954f,.26130258f,.27577711f};
        for(int c=0;c<3;c++)for(int i=0;i<normal.rgb.length;i++)out[c*50176+i]=(((normal.rgb[i]>>>(16-c*8))&255)/255f-mean[c])/sd[c];
        return out;
    }
    static double rounded(double x,int places){double k=Math.pow(10,places);return Math.rint(x*k)/k;}
    static double quantile(int[] counts,int n,double q){double f=(n-1)*q;int lo=(int)f,hi=(int)Math.ceil(f),v0=0,v1=0,total=0;
        for(int i=0;i<counts.length;i++){int old=total;total+=counts[i];if(old<=lo&&total>lo)v0=i;if(old<=hi&&total>hi){v1=i;break;}}return v0+(v1-v0)*(f-lo);}
    static JSONObject appearance(Image source)throws JSONException{
        Image a=source.resize(256,256,LINEAR);int[] xs=new int[256],ys=new int[256];boolean[] occupied=new boolean[256];int n=0,color=0;
        for(int y=0;y<256;y++)for(int x=0;x<256;x++){int p=a.rgb[y*256+x];if(min(p)<235){n++;xs[x]++;ys[y]++;occupied[(y/16)*16+x/16]=true;if(max(p)-min(p)>65)color++;}}
        if(n<180)return invalid("Draw the main body of a plant before recognizing it.");
        double width=(quantile(xs,n,.98)-quantile(xs,n,.02)+1)/256,height=(quantile(ys,n,.98)-quantile(ys,n,.02)+1)/256,coverage=n/65536.0;
        if(Math.min(width,height)<.04)return invalid("The outline is too narrow. Add a body, leaves, or other features.");
        if(coverage>.7)return invalid("Leave some white space so the plant's outline is clear.");
        int cells=0;for(boolean c:occupied)if(c)cells++;
        double body=Math.sqrt(width*height),density=Math.min(1,coverage/Math.max(.04,width*height)/.45),structure=Math.min(1,cells/256.0/.6),colored=(double)color/n;
        double power=rounded(Math.min(5,1+1.8*body+.8*density+.8*structure+.4*colored),2);
        return new JSONObject().put("valid",true).put("strength",power).put("body",rounded(body,3)).put("structure",rounded(structure,3))
            .put("density",rounded(density,3)).put("colorPresence",rounded(colored,3)).put("healthMultiplier",rounded(1+(power-1)*.7,2))
            .put("damageMultiplier",rounded(1+(power-1)*.5,2)).put("speedMultiplier",rounded(1+(power-1)*.1,2))
            .put("message","Strength reflects body size, structure, density, and color.");
    }
    static JSONObject invalid(String message)throws JSONException{return new JSONObject().put("valid",false).put("message",message);}
    static boolean primitive(Image a){
        int x0=224,y0=224,x1=-1,y1=-1,n=0;
        for(int y=0;y<224;y++)for(int x=0;x<224;x++)if(min(a.rgb[y*224+x])<230){n++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}
        if(n<10)return true;double w=x1-x0+1,h=y1-y0+1;int center=0,diskIn=0,rectangle=0,ellipse=0;
        for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++)if(min(a.rgb[y*224+x])<230){
            double nx=(x-x0+.5-w/2)/(w/2),ny=(y-y0+.5-h/2)/(h/2),disk=nx*nx+ny*ny;
            if(Math.abs(nx)<.6&&Math.abs(ny)<.6)center++;if(disk<.4)diskIn++;if(Math.abs(nx)>.7||Math.abs(ny)>.7)rectangle++;if(disk>.5&&disk<1.18)ellipse++;
        }
        return (double)center/n<.008&&((double)rectangle/n>.985&&n/(w*h)>.035||(double)diskIn/n<.008&&(double)ellipse/n>.985&&n/(w*h)>.025);
    }
    static float[] colors(Image a){
        float[] out=new float[16];int[] edges={12,27,40,115,190,222,243};
        for(int y=0;y<224;y++)for(int x=0;x<224;x++){
            int p=a.rgb[y*224+x],r=(p>>>16)&255,g=(p>>>8)&255,b=p&255,hi=max(p),lo=min(p),delta=hi-lo;
            if(hi<=65||delta*255/hi<=65)continue;
            double hue=hi==r?(double)(g-b)/delta:hi==g?2+(double)(b-r)/delta:4+(double)(r-g)/delta;
            if(hue<0)hue+=6;int h=(int)(hue*255/6),bucket=0;while(bucket<7&&h>=edges[bucket])bucket++;if(bucket==7)bucket=0;
            out[(y<142?0:8)+bucket]++;
        }
        for(int offset:new int[]{0,8}){double norm=0;for(int i=0;i<8;i++)norm+=out[offset+i]*out[offset+i];norm=Math.max(1,Math.sqrt(norm));for(int i=0;i<8;i++)out[offset+i]/=norm;}
        return out;
    }
    static float[] shape(Image a){
        boolean[] fg=new boolean[224*224],dilated=new boolean[226*226],outside=new boolean[226*226];
        for(int i=0;i<fg.length;i++)fg[i]=min(a.rgb[i])<235;
        for(int y=0;y<224;y++)for(int x=0;x<224;x++)if(fg[y*224+x])for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
            int yy=y+dy,xx=x+dx;if(yy>=0&&yy<224&&xx>=0&&xx<224)dilated[(yy+1)*226+xx+1]=true;
        }
        int[] queue=new int[226*226];int head=0,tail=1;outside[0]=true;
        while(head<tail){int p=queue[head++],x=p%226,y=p/226;
            for(int next:new int[]{x>0?p-1:-1,x<225?p+1:-1,y>0?p-226:-1,y<225?p+226:-1})
                if(next>=0&&!outside[next]&&!dilated[next]){outside[next]=true;queue[tail++]=next;}
        }
        int[] pixels=new int[224*224];for(int y=0;y<224;y++)for(int x=0;x<224;x++)pixels[y*224+x]=outside[(y+1)*226+x+1]?0xff000000:-1;
        Image small=new Image(224,224,pixels).resize(32,32,BOX);float[] result=new float[1024];for(int i=0;i<1024;i++)result[i]=(small.rgb[i]&255)/255f;return result;
    }
    static float[] spatial(Image a){Image small=a.resize(24,24,BOX);float[] out=new float[1728];for(int c=0;c<3;c++)for(int i=0;i<576;i++)out[c*576+i]=1-((small.rgb[i]>>>(16-c*8))&255)/255f;return out;}
    static float[] agreement(float[] query,float[][] refs,int size,int channels,int shift){
        float[] scores=new float[refs.length],sums=new float[refs.length];for(int i=0;i<refs.length;i++)for(float x:refs[i])sums[i]+=x;
        for(int dy=-shift;dy<=shift;dy+=shift)for(int dx=-shift;dx<=shift;dx+=shift){
            float[] shifted=new float[query.length];float sum=0;
            for(int c=0;c<channels;c++)for(int y=0;y<size;y++)for(int x=0;x<size;x++){int yy=y+dy,xx=x+dx;if(yy>=0&&yy<size&&xx>=0&&xx<size){float v=query[c*size*size+yy*size+xx];shifted[c*size*size+y*size+x]=v;sum+=v;}}
            for(int i=0;i<refs.length;i++){float intersection=0;for(int j=0;j<query.length;j++)intersection+=Math.min(refs[i][j],shifted[j]);scores[i]=Math.max(scores[i],2*intersection/(sums[i]+sum+1e-6f));}
        }return scores;
    }
    static float mean(float[] a){float sum=0;for(float x:a)sum+=x;return sum/a.length;}
    static float ink(Image a){int n=0;for(int x:a.rgb)if(min(x)<235)n++;return (float)n/a.rgb.length;}
}
