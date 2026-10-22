package com.silvershadow.pvzf;

/** Shared, context-reviewed drawing UI wording for both regular and AI builds. */
public final class PlantbrushTranslations {
    public static final String[][] EXACT = {
        {"请确认是否启动了最新版神笔马良识图AI，可前往融合wiki下载", "The recognizer is included in the AI APK. Restart the game and try again."},
        {"[神笔马良] 没有有效的植物候选，请重新鉴定。", "[Magic Plantbrush] No valid plants found. Try identifying again."},
        {"[神笔马良] 画作已改变，本次鉴定结果已丢弃。", "[Magic Plantbrush] Drawing changed. Identify it again."},
        {"本地识别服务尚不支持指定植物评分，请启动更新后的神笔马良识别服务。", "This recognizer does not support scoring a selected plant. Update the AI prototype."},
        {"。请启动神笔马良本地服务。", ". Open Magic Plantbrush to start recognition."},
        {"选择这株植物", "Choose this plant"},
    };
    public static final String[][] RULES = {
        {"(?s)(?:\\[(?:神笔马良|Magic Plantbrush)\\] )?本地识别服务未就绪或请求失败：(.*?)。请启动神笔马良本地服务。(?:\\n<color=red>请确认是否启动了最新版神笔马良识图AI，可前往融合wiki下载</color>)?", "[Magic Plantbrush] Recognition service unavailable: {0}\nRestart the game and try again."},
        {"本地识别服务未就绪或请求失败：(.*)", "Recognition service unavailable: {0}"},
        {"铅笔\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Pencil / Width {0} / 256 × 256"},
        {"橡皮\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Eraser / Width {0} / 256 × 256"},
        {"直线\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Line / Width {0} / 256 × 256"},
        {"矩形\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Rectangle / Width {0} / 256 × 256"},
        {"椭圆\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Ellipse / Width {0} / 256 × 256"},
        {"填充\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Fill / Width {0} / 256 × 256"},
        {"取色\\s*/\\s*笔宽 (\\d+)\\s*/\\s*256 × 256", "Picker / Width {0} / 256 × 256"},
        {"\\[神笔马良\\] 鉴定失败：(.*)", "[Magic Plantbrush] {0}"},
        {"相似度：([0-9.,]+\\s*%)", "Similarity: {0}"},
        {"强度：[ ]*([0-9.,]+)", "Strength: {0}"},
        {"获得植物：(.*)", "Plant received: {0}"},
        {"已替换贴图：(.*)", "Appearance updated: {0}"},
        {"强度 = ([0-9.,]+)", "Strength = {0}"},
        {"相似度 = ([0-9.,]+\\s*%?)", "Similarity = {0}"},
    };
}
