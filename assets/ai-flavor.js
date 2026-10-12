/* AI 味检测器 —— 纯浏览器运行，稿件不上传。
   规则移植自执笔惊鸿写作工作台的本地红线扫描引擎。 */
(function () {
  var FLAVOR_WORDS = [
    ["仿佛", "虚词"], ["似乎", "虚词"], ["宛如", "虚词"], ["犹如", "虚词"], ["好像", "虚词"],
    ["忽然", "时间副词"], ["骤然", "时间副词"], ["猛地", "时间副词"], ["瞬间", "时间副词"],
    ["刹那间", "时间副词"], ["陡然", "时间副词"], ["这一刻", "时间副词"], ["那一瞬间", "时间副词"],
    ["然而", "转折连词"],
    ["心中五味杂陈", "空泛抒情"], ["内心深处", "空泛抒情"], ["眼神深邃", "空泛抒情"], ["天地都安静了", "空泛抒情"],
    ["这意味着", "总结概括"], ["换句话说", "总结概括"], ["值得注意的是", "总结概括"],
    ["眼神一凝", "表情套话"], ["嘴角勾起", "表情套话"], ["眼中闪过一丝", "表情套话"], ["眸光一闪", "表情套话"],
    ["心里一暖", "情绪直给"], ["激动万分", "情绪直给"], ["感动不已", "情绪直给"], ["心头一紧", "情绪直给"]
  ];
  var PATTERNS = [
    [/不是[^。！？\n]{2,30}而是/g, "「不是…而是…」绕圈句式", "书面总结腔，改成直接给结果"],
    [/(愤怒|冷冷|淡淡|平静|严肃|激动|轻声|沉声)地说/g, "「X 地说」式副词", "用动作或反应替代，别替读者念情绪"],
    [/既[^，。！？\n]{1,14}又[^，。！？\n]{1,14}/g, "「既…又…」对称句式", "拆成错落短句，避免排比腔"]
  ];
  var STOPWORDS = new Set(("一个 什么 没有 自己 他们 我们 你们 她们 这个 那个 这么 那么 已经 还是 知道 看到 时候 现在 但是 因为 所以 如果 虽然 只是 不过 然后 觉得 起来 出来 下来 过去 回来 开始 发现 看见 声音 眼前 心里 感觉 一样 忽然 仿佛 似乎 真的 有点 有些 一下 一边 于是 而且 甚至 还有 就是 不是 可是 可以 不能 不会 这么 那样 这里 那里 身上 手上 脚下 脸上 眼里 屋里 门外 村里 山上 时间 地方 东西 事情 面前 身后 旁边 周围 最后 终于 原来 其实 大概 也许 可能 应该 必须 一定 一起 一直 一般 一点 一些 不多 不少 十分 非常 特别 更加 越来越 渐渐 慢慢 轻轻 缓缓 微微 暗暗 冷冷 静静 淡淡 死死 紧紧 深深 重重 狠狠 纷纷 连忙 赶紧 急忙 立刻 马上 顿时 随即 随后 接着 跟着 之后 以前 以后 原本 当初 曾经 后来 如今 此刻 此时 这时 那时 当晚 次日").split(/\s+/));

  function scan(content) {
    if (!content || !content.trim()) return null;
    var clean = content.replace(/\s/g, "");
    var wordCount = clean.length;
    var dashCount = (content.match(/—{2,}/g) || []).length;
    var ellipsisCount = (content.match(/…{2,}/g) || []).length;

    var flavorHits = [];
    FLAVOR_WORDS.forEach(function (pair) {
      var n = content.split(pair[0]).length - 1;
      if (n > 0) flavorHits.push({ word: pair[0], category: pair[1], count: n });
    });
    flavorHits.sort(function (a, b) { return b.count - a.count; });

    var patternIssues = [];
    PATTERNS.forEach(function (p) {
      var m = content.match(p[0]) || [];
      if (m.length) patternIssues.push({ name: p[1], count: m.length, sample: (m[0] || "").slice(0, 24), suggestion: p[2] });
    });

    var freq = {};
    for (var i = 0; i < clean.length - 1; i++) {
      var w = clean.slice(i, i + 2);
      if (STOPWORDS.has(w)) continue;
      freq[w] = (freq[w] || 0) + 1;
    }
    var topRepeated = Object.keys(freq).map(function (w) { return { word: w, count: freq[w] }; })
      .filter(function (r) { return r.count >= 4; })
      .sort(function (a, b) { return b.count - a.count; }).slice(0, 10);

    var issues = [];
    if (wordCount < 2000) issues.push({ severity: "medium", label: "字数不足", detail: "当前 " + wordCount + " 字，番茄男频建议单章 2000–2500 字。", suggestion: "先把本章内容补足再复检。" });
    if (dashCount > 10) issues.push({ severity: "high", label: "破折号泛滥", detail: "本章 " + dashCount + " 处破折号，AI 味重灾区。", suggestion: "删到 5 处以内；破折号留给最想强调的那一句。" });
    else if (dashCount > 5) issues.push({ severity: "medium", label: "破折号偏多", detail: "本章 " + dashCount + " 处破折号（红线 ≤5）。", suggestion: "优先删掉可换成逗号、句号的破折号。" });
    if (ellipsisCount > 3) issues.push({ severity: "medium", label: "省略号滥用", detail: "本章 " + ellipsisCount + " 处省略号（红线 ≤3）。", suggestion: "省略号留给欲言又止的对话，其余删掉。" });

    var totalFlavor = flavorHits.reduce(function (s, h) { return s + h.count; }, 0);
    if (totalFlavor >= 10) issues.push({ severity: "high", label: "AI 高频词偏多", detail: "共命中 " + totalFlavor + " 处（仿佛、然而、这一刻等）。", suggestion: "逐处换成具体动作或删掉；重复超过 3 次的词优先处理。" });
    else if (totalFlavor >= 5) issues.push({ severity: "medium", label: "有 AI 腔词汇", detail: "共命中 " + totalFlavor + " 处 AI 高频词。", suggestion: "见下方命中列表，逐词替换。" });

    patternIssues.forEach(function (p) {
      issues.push({ severity: p.count >= 3 ? "high" : "medium", label: p.name, detail: p.count + " 处，例如「" + p.sample + "」", suggestion: p.suggestion });
    });
    topRepeated.slice(0, 5).forEach(function (r) {
      if (r.count >= 8) issues.push({ severity: "medium", label: "重复词「" + r.word + "」", detail: "出现 " + r.count + " 次。", suggestion: "用近义表达替换一半以上，别让读者看出复读机。" });
    });

    var score = 100;
    if (wordCount < 2000) score -= 5;
    if (dashCount > 5) score -= Math.min(10, (dashCount - 5) * 2);
    if (ellipsisCount > 3) score -= 5;
    score -= Math.min(20, totalFlavor * 2);
    score -= Math.min(15, patternIssues.reduce(function (s, p) { return s + p.count; }, 0) * 3);
    score -= Math.min(10, topRepeated.filter(function (r) { return r.count >= 8; }).length * 3);
    score = Math.max(0, Math.min(100, score));

    return { score: score, wordCount: wordCount, dashCount: dashCount, ellipsisCount: ellipsisCount,
             flavorHits: flavorHits, patternIssues: patternIssues, topRepeated: topRepeated, issues: issues };
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function render(r) {
    var grade = r.score >= 85 ? ["ok", "很干净"] : r.score >= 70 ? ["warn", "尚可，有 AI 腔"] : r.score >= 50 ? ["warn", "AI 味明显"] : ["bad", "AI 味很重"];
    var h = '<div class="score"><div class="num ' + grade[0] + '">' + r.score + '</div><div class="txt"><b>' + grade[1] + '</b>'
          + '字数 ' + r.wordCount + ' ｜ 破折号 ' + r.dashCount + ' 处 ｜ 省略号 ' + r.ellipsisCount + ' 处</div></div>';

    var tags = r.flavorHits.map(function (f) { return '<span class="tag hit">' + esc(f.word) + ' ×' + f.count + '</span>'; }).join("");
    h += '<h3 style="margin:22px 0 8px;font-size:16px;color:#1c1a17">AI 高频词命中（' + r.flavorHits.length + ' 类）</h3>';
    h += tags ? '<div>' + tags + '</div>' : '<div><span class="tag ok">无命中，很好</span></div>';

    h += '<h3 style="margin:22px 0 8px;font-size:16px;color:#1c1a17">问题清单（' + r.issues.length + ' 项）</h3>';
    h += r.issues.length ? r.issues.map(function (i) {
      return '<div class="issue ' + i.severity + '"><div class="lb">' + esc(i.label) + '：' + esc(i.detail) + '</div><div class="sg">建议：' + esc(i.suggestion) + '</div></div>';
    }).join("") : '<div class="issue low"><div class="lb">未发现明显问题</div><div class="sg">可以再通读一遍语气与节奏。</div></div>';

    if (r.topRepeated.length) {
      h += '<h3 style="margin:22px 0 8px;font-size:16px;color:#1c1a17">重复词 Top' + r.topRepeated.length + '</h3>';
      h += '<div>' + r.topRepeated.map(function (x) { return '<span class="tag">' + esc(x.word) + ' ×' + x.count + '</span>'; }).join("") + '</div>';
    }
    return h;
  }

  var SAMPLE = "那一刻，他仿佛听见了什么声音。\n他猛地回过头，眼神一凝，嘴角勾起一抹冷笑。\n似乎有什么东西在暗中窥视着他。然而他并不害怕——他从来都不害怕——恐惧这种东西，早就离他远去了。\n内心深处，一股愤怒油然而生。他既愤怒又冷静，既恐惧又兴奋。";

  document.addEventListener("DOMContentLoaded", function () {
    var ta = document.getElementById("src");
    var box = document.getElementById("result");
    var run = document.getElementById("run");
    var sample = document.getElementById("sample");
    var clear = document.getElementById("clear");
    if (!ta) return;
    function go() {
      var r = scan(ta.value);
      if (!r) { box.classList.remove("show"); return; }
      box.innerHTML = render(r);
      box.classList.add("show");
    }
    run.addEventListener("click", go);
    ta.addEventListener("input", go);
    sample.addEventListener("click", function () { ta.value = SAMPLE; go(); });
    clear.addEventListener("click", function () { ta.value = ""; box.classList.remove("show"); ta.focus(); });
    go();
  });
})();
