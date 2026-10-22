"""Exercise actual Java display translation with compound editor-help fixtures."""
import argparse, base64, json, os, subprocess
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    for key in ('work','jdk','sdk'):ap.add_argument('--'+key,type=Path,required=True)
    ap.add_argument('--audit-folder',default='editor-r14')
    a=ap.parse_args();w=a.work;out=w/a.audit_folder;out.mkdir(exist_ok=True)
    payload=json.loads((w/'english/translations.json').read_text(encoding='utf8'))
    report=json.loads((w/'guide-r13/apply-report.json').read_text(encoding='utf8'))
    fixtures=[(v['source'],v['after']) for v in report['dictionary_changes']]
    intro_report=w/'level-intros-r19/apply-report.json'
    if intro_report.exists():
        intros=json.loads(intro_report.read_text(encoding='utf8'))
        fixtures += [(v['source'],v['english']) for v in intros['entries']]
    final_spec=Path(__file__).resolve().parents[1]/'assets/final-ui-audit-4.0.5.json'
    if payload.get('final_ui_audit_revision'):
        final=json.loads(final_spec.read_text(encoding='utf8'))
        assert final['revision']==payload['final_ui_audit_revision']
        fixtures += [(x['source'],x['english']) if x['kind']=='exact' else tuple(x['fixture']) for x in final['entries']]
        fixtures += [(s,s) for s in final['fixtures_preserve']]
    fixtures += [
        ('事件规则工具  ·  先添加规则模板 → 选中节点看说明、改数值 → 检查连线 → 保存并试玩',
         'Event Rule Tools · Add a template → read node help and edit values → check connections → save and playtest'),
        ('事件规则工具  ·  节点草稿已保存。保存整关请点击底部“保存并生成关卡”',
         'Event Rule Tools · Node draft saved. Press Save Level at the bottom to save the whole level.'),
        ('Node Details 已显示','Node Details (Shown)'),
        ('Level Variables 已隐藏','Level Variables (Hidden)'),
        ('0 个变量','Variables: 0'),('12个变量','Variables: 12'),
        ('我的模板 2/4 页','My Templates: 2/4'),
        ('当前连接： On Level Official Start → Trigger','Connected: On Level Official Start → Trigger'),
        ('当前填写： 5','Entered value: 5'),
        ('<b>Trigger</b> （执行信号）','<b>Trigger</b> (Execution Signal)'),
        ('<b>Interval</b> （小数）','<b>Interval</b> (Float)'),
        ('Condition （布尔）','Condition (Boolean)'),
        ('<b>Node Details</b> 已显示','<b>Node Details</b> Shown'),
        ('<b>Level Variables</b> 已隐藏','<b>Level Variables</b> Hidden'),
        ('<size=20>排查时可使用节点编号： ab1dc7e9-5814-4ab3-b94c-3e3c6f997f13</size>',
         '<size=20>Node ID for troubleshooting: ab1dc7e9-5814-4ab3-b94c-3e3c6f997f13</size>'),
    ]
    # Help combines several independent formatted sections into one TMP label.
    fixtures.append(('<b>用来做什么</b>\nTurns a repeating timed action on or off.\n\n'
                     '<b>怎么使用</b>\nConnect Cycle Event to the repeated action.\n\n'
                     '<b>左侧输入：需要接什么</b>\nTrigger （执行信号）\n当前填写： 5',
                     '<b>Purpose</b>\nTurns a repeating timed action on or off.\n\n'
                     '<b>How to Use</b>\nConnect Cycle Event to the repeated action.\n\n'
                     '<b>Inputs: what to connect</b>\nTrigger (Execution Signal)\nEntered value: 5'))
    for text in ['Disabled','二爷无视植物','电力相生','外挂','My Custom Rule','我的规则','ab1dc7e9-5814-4ab3-b94c-3e3c6f997f13',
                 'My rule 当前填写： 5 (identifier)', 'Some unrelated 已显示 label']:
        fixtures.append((text,text))
    def row(kind,*fields):return '\t'.join([kind]+[base64.b64encode(s.encode()).decode() for s in fields])
    lines=[row('E',k,v) for k,v in payload['exact'].items()]
    lines += [row('R',*r) for r in payload['regex']]
    lines += [row('C',*f) for f in fixtures]
    fixture_path=out/'display-fixtures.tsv';fixture_path.write_text('\n'.join(lines),encoding='utf8')
    cp=os.pathsep.join(map(str,[w/'java-tests',w/'java-classes',a.sdk/'platforms/android-35/android.jar']))
    with (out/'fixture-test.log').open('w',encoding='utf8') as log:
        result=subprocess.run([str(a.jdk/'bin/java.exe'),'-cp',cp,'PayloadTranslationTest',str(fixture_path),str(out/'fixture-results.txt')],stdout=log,stderr=subprocess.STDOUT,timeout=30)
    print((out/'fixture-test.log').read_text(encoding='utf8')[-2000:])
    if result.returncode:raise SystemExit(result.returncode)

if __name__=='__main__':main()
