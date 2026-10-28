package com.silvershadow.pvzf;

/** Conservative necessary prefix for Matcher.matches(), not a replacement matcher. */
public final class RegexPrefix {
    public static String of(String regex) {
        // Any alternation or case/flag group uses the original matcher unfiltered.
        // False negatives must never suppress a translation.
        if(regex.indexOf('|')>=0 || regex.contains("(?"))return "";
        StringBuilder prefix=new StringBuilder();int i=regex.startsWith("^")?1:0;
        for(;i<regex.length();i++) {
            char c=regex.charAt(i);
            if(c=='\\') {
                if(i+1>=regex.length())break;
                char next=regex.charAt(i+1);
                if(".[](){}*+?^$\\".indexOf(next)<0)break;
                prefix.append(next);i++;continue;
            }
            if("*+?{".indexOf(c)>=0) {
                // The immediately preceding literal may be optional. Dropping it
                // even for + is conservative; the regex still decides the match.
                if(prefix.length()>0)prefix.setLength(prefix.offsetByCodePoints(prefix.length(),-1));
                break;
            }
            if(".[]()^$".indexOf(c)>=0)break;
            prefix.append(c);
        }
        return prefix.toString();
    }
}
