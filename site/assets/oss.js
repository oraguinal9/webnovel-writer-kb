// 开源工具导航：分类筛选 + 关键词搜索
(function () {
  var q = document.getElementById('ossq');
  var list = document.getElementById('osslist');
  var empty = document.getElementById('ossempty');
  if (!q || !list) return;
  var cards = [].slice.call(list.querySelectorAll('.osscard'));
  var btns = [].slice.call(document.querySelectorAll('.btn.chip[data-cat]'));
  var cat = 'all';

  function apply() {
    var kw = (q.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (c) {
      var okCat = (cat === 'all') || (c.getAttribute('data-cat') === cat);
      var okKw = !kw || (c.getAttribute('data-k') || '').toLowerCase().indexOf(kw) > -1
        || c.textContent.toLowerCase().indexOf(kw) > -1;
      var show = okCat && okKw;
      c.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    if (empty) empty.style.display = shown ? 'none' : 'block';
  }

  q.addEventListener('input', apply);
  btns.forEach(function (b) {
    b.addEventListener('click', function () {
      btns.forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      cat = b.getAttribute('data-cat');
      apply();
    });
  });
})();
