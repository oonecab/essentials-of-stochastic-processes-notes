
(() => {
  // Preserve the source notation when copying complete formulas.
  // Partial formula selections keep the browser's normal copy behavior.
  document.addEventListener('copy', event => {
    const selection = getSelection();
    if (!event.clipboardData || !selection || selection.isCollapsed || selection.rangeCount !== 1) return;
    const range = selection.getRangeAt(0);
    const maths = Array.from(document.querySelectorAll('main math, #annotation-content math'))
      .filter(math => range.intersectsNode(math));
    if (!maths.length) return;
    const labels = [];
    for (const math of maths) {
      const annotation = math.querySelector('annotation[encoding="text/plain"]');
      if (!annotation) return;
      const walker = document.createTreeWalker(math, NodeFilter.SHOW_TEXT, {
        acceptNode: node => node.textContent.trim() && !node.parentElement.closest('annotation')
          ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
      });
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      if (!nodes.length) return;
      const visible = document.createRange();
      visible.setStart(nodes[0], 0);
      visible.setEnd(nodes[nodes.length - 1], nodes[nodes.length - 1].length);
      if (range.compareBoundaryPoints(Range.START_TO_START, visible) > 0 ||
          range.compareBoundaryPoints(Range.END_TO_END, visible) < 0) return;
      labels.push(annotation.textContent);
    }
    const host = document.createElement('div');
    host.append(range.cloneContents());
    if (!host.querySelector('math') && maths.length === 1 && maths[0].contains(range.commonAncestorContainer)) {
      host.replaceChildren(maths[0].cloneNode(true));
    }
    const copies = Array.from(host.querySelectorAll('math'));
    if (copies.length !== labels.length) return;
    host.querySelectorAll('script, style, noscript').forEach(node => node.remove());
    host.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'));
    const richText = host.innerHTML;
    copies.forEach((math, i) => math.replaceWith(document.createTextNode(labels[i])));
    host.setAttribute('aria-hidden', 'true');
    host.inert = true;
    host.style.cssText = 'position:fixed;left:-100000px;top:0;width:860px;pointer-events:none;opacity:0';
    document.body.append(host);
    try {
      event.clipboardData.setData('text/plain', host.innerText);
      event.clipboardData.setData('text/html', richText);
      event.preventDefault();
    } finally {
      host.remove();
    }
  });
})();
