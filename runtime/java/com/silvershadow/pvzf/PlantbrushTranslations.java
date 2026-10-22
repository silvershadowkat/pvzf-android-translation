package com.silvershadow.pvzf;

/** Shared, context-reviewed drawing UI wording for both regular and AI builds. */
public final class PlantbrushTranslations {
    public static final String[][] EXACT = {
        {"系统认为你画的像僵尸，于是立马安排了一群僵尸进攻", "Your drawing looks like a zombie! A group of zombies is attacking!"},
        {"可以按F1隐藏菜单，照着植物画", "With a keyboard, press F1 to hide the drawing window and use the plant as a reference."},
        {"神笔马良自由画板", "Magic Plantbrush Drawing Canvas"},
        {"网格：关", "Grid: Off"},
        {"网格：开", "Grid: On"},
        {"请确认是否启动了最新版神笔马良识图AI，可前往融合wiki下载", "The recognizer is included in the AI APK. Restart the game and try again."},
        {"[神笔马良] 没有有效的植物候选，请重新鉴定。", "[Magic Plantbrush] No valid plants found. Try identifying again."},
        {"[神笔马良] 画作已改变，本次鉴定结果已丢弃。", "[Magic Plantbrush] Drawing changed. Identify it again."},
        {"本地识别服务尚不支持指定植物评分，请启动更新后的神笔马良识别服务。", "This recognizer does not support scoring a selected plant. Update the AI prototype."},
        {"。请启动神笔马良本地服务。", ". Open Magic Plantbrush to start recognition."},
        {"选择这株植物", "Choose this plant"},
    };
    // Native request errors are concatenated with a prefix and sometimes a red hint.
    // Match the complete composed display before the general failure rule; translating
    // only the prefix would leave a Chinese error inside its captured value.
    public static final String[][] REQUEST_ERRORS = {
        {"识别服务返回的数据无法解析。", "The recognition response could not be read. Try again."},
        {"识别服务返回空结果", "The recognizer returned no result. Try again."},
        {"识别结果无效，请重建图库索引后重试。", "The recognition result is invalid. Restart or update the AI app."},
        {"识别请求尚未完成", "Recognition is still in progress. Please wait."},
        {"本地识别服务尚不支持指定植物评分，请启动更新后的神笔马良识别服务。", "This recognizer does not support scoring a selected plant. Update the AI prototype."},
    };
    private static final String PREFIX = "(?:\\[(?:神笔马良|Magic Plantbrush)\\] )?(?:鉴定失败：)?";
    private static final String HINT = "(?:\\n<color=red>请确认是否启动了最新版神笔马良识图AI，可前往融合wiki下载</color>)?";
    public static final String[][] RULES = makeRules();
    private static String[][] makeRules() {
        java.util.List<String[]> rules = new java.util.ArrayList<>();
        for (String[] error : REQUEST_ERRORS) {
            rules.add(new String[]{PREFIX + java.util.regex.Pattern.quote(error[0]) + HINT,
                    "[Magic Plantbrush] " + error[1]});
        }
        java.util.Collections.addAll(rules, new String[][] {
        {"(?s)" + PREFIX + "本地识别服务未就绪或请求失败：(.*?)。请启动神笔马良本地服务。" + HINT, "[Magic Plantbrush] Recognition service unavailable: {0}\nRestart the game and try again."},
        {"本地识别服务未就绪或请求失败：(.*)", "Recognition service unavailable: {0}"},
        {"铅笔\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Pencil / Width {0} / 256 × 256"},
        {"橡皮\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Eraser / Width {0} / 256 × 256"},
        {"直线\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Line / Width {0} / 256 × 256"},
        {"矩形\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Rectangle / Width {0} / 256 × 256"},
        {"椭圆\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Ellipse / Width {0} / 256 × 256"},
        {"填充\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Fill / Width {0} / 256 × 256"},
        {"填色\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Fill / Width {0} / 256 × 256"},
        {"取色\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Picker / Width {0} / 256 × 256"},
        {"\\[神笔马良\\] 鉴定失败：(.*)", "[Magic Plantbrush] {0}"},
        {"相似度：([0-9.,]+\\s*%)", "Similarity: {0}"},
        {"强度：[ ]*([0-9.,]+)", "Strength: {0}"},
        {"获得植物：(.*)", "Plant received: {0}"},
        {"已替换贴图：(.*)", "Appearance updated: {0}"},
        {"强度 = ([0-9.,]+)", "Strength = {0}"},
        {"相似度 = ([0-9.,]+\\s*%?)", "Similarity = {0}"},
        });
        return rules.toArray(new String[0][]);
    }
}
