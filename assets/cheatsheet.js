/* 平台规则速查：关键词搜索 + 类型筛选 */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    var q = document.getElementById("q");
    var rows = [].slice.call(document.querySelectorAll("tbody tr"));
    var chips = [].slice.call(document.querySelectorAll(".chip"));
    var active = "all";
    function apply() {
      var key = (q && q.value || "").trim().toLowerCase();
      rows.forEach(function (tr) {
        var txt = tr.textContent.toLowerCase();
        var okQ = !key || txt.indexOf(key) >= 0;
        var okC = active === "all" || (tr.getAttribute("data-type") || "").indexOf(active) >= 0;
        tr.style.display = (okQ && okC) ? "" : "none";
      });
    }
    if (q) q.addEventListener("input", apply);
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        chips.forEach(function (x) { x.classList.remove("btn-primary"); });
        c.classList.add("btn-primary");
        active = c.getAttribute("data-type");
        apply();
      });
    });
  });
})();
